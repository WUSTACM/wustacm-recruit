# -*- coding: utf-8 -*-
"""age 批量解密图形界面。

设计取舍：
- 不引入 age 的 Python 绑定（pyage 等），而是调用仓库自带的 age 二进制。
  这样解密行为与新生提交时的加密实现完全一致，且打包后无需额外依赖。
- 私钥默认只存在于内存：粘进输入框的文本不会被写入任何临时文件。
  只有用户主动「选择 identity 文件」时，才从磁盘读取。
- 解密在后台线程执行，避免大批量文件时界面假死。
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "age 批量解密工具"

# age 的退出码无法区分「私钥不匹配」和「文件损坏」，因此靠 stderr 关键字判断，
# 目的是给管理员一句可操作的中文提示，而不是原样抛出英文报错。
ERR_NO_MATCH = "no identity matched"
ERR_NO_MATCH_HINT = "该文件不是用这把私钥加密的（可能是旧公钥加密的历史提交），只能让提交者重新提交。"


def find_age_exe() -> Path | None:
    """定位 age 可执行文件。

    查找顺序体现「就近优先」：从自身所在目录沿目录树向上查找仓库内的
    tools\\windows-amd64\\age.exe，最后才依赖 PATH，这样无论 exe 是被
    放在 tools\\decrypt-gui\\dist\\ 还是被拷到仓库根目录都能找到。
    """
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        # PyInstaller 打包后，__file__ 指向临时解包目录，不能用来推断仓库位置。
        # exe 可能被放在 tools\decrypt-gui\dist\，也可能被拷到别处，
        # 因此沿目录树向上逐级查找 tools\windows-amd64\age.exe。
        base = Path(sys.executable).resolve().parent
        candidates.append(base / "age.exe")
        for parent in [base, *base.parents]:
            candidates.append(parent / "windows-amd64" / "age.exe")
            candidates.append(parent / "tools" / "windows-amd64" / "age.exe")
    else:
        here = Path(__file__).resolve().parent
        candidates.append(here.parent / "windows-amd64" / "age.exe")
        candidates.append(here.parent / "tools" / "windows-amd64" / "age.exe")

    for path in candidates:
        if path.is_file():
            return path.resolve()

    # 兜底：PATH 中若有 age，也可用
    from shutil import which

    found = which("age") or which("age.exe")
    return Path(found) if found else None


def parse_identity_text(text: str) -> str | None:
    """从粘贴的文本里提取 AGE-SECRET-KEY。

    容忍用户整段粘贴 identity 文件内容（含 # 注释行），只取真正的私钥行，
    避免因为多带了注释就报「格式错误」。
    """
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("AGE-SECRET-KEY-"):
            return line
    return None


class DecryptApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self.age_exe = find_age_exe()
        self.identity_file: Path | None = None
        self.targets: list[Path] = []
        self.out_dir: Path | None = None
        self.log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.cancel_flag = threading.Event()

        self._build_widgets()
        self.after(100, self._drain_log)

    # ---------- 界面 ----------

    def _build_widgets(self) -> None:
        row = 0
        ttk.Label(self, text=APP_TITLE, font=("", 13, "bold")).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        row += 1

        # age 二进制状态：缺失时直接禁用开始按钮，避免用户白填一堆表单
        age_text = str(self.age_exe) if self.age_exe else "未找到 age.exe（请选择或加入 PATH）"
        self.age_label = ttk.Label(self, text=f"age 程序：{age_text}", foreground="#555")
        self.age_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1

        key_box = ttk.LabelFrame(self, text="1. 私钥", padding=8)
        key_box.grid(row=row, column=0, sticky="ew", pady=4)
        key_box.columnconfigure(0, weight=1)
        row += 1

        self.key_text = tk.Text(key_box, height=3, wrap="none")
        self.key_text.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(
            key_box,
            text="粘贴 AGE-SECRET-KEY-... （可整段粘贴 identity 文件内容）",
            foreground="#777",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 6))
        ttk.Button(key_box, text="从文件读取 identity…", command=self._pick_identity).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Button(key_box, text="清空", command=self._clear_key).grid(
            row=2, column=1, sticky="e"
        )
        key_box.columnconfigure(1, weight=1)

        target_box = ttk.LabelFrame(self, text="2. 待解密文件", padding=8)
        target_box.grid(row=row, column=0, sticky="ew", pady=4)
        target_box.columnconfigure(0, weight=1)
        row += 1

        self.target_label = ttk.Label(target_box, text="尚未选择", foreground="#777")
        self.target_label.grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Button(target_box, text="选择 .age 文件…", command=self._pick_files).grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Button(target_box, text="选择文件夹…", command=self._pick_folder).grid(
            row=1, column=1, sticky="w", pady=(6, 0)
        )
        ttk.Button(target_box, text="清空", command=self._clear_targets).grid(
            row=1, column=2, sticky="e", pady=(6, 0)
        )
        target_box.columnconfigure(2, weight=1)

        out_box = ttk.LabelFrame(self, text="3. 输出", padding=8)
        out_box.grid(row=row, column=0, sticky="ew", pady=4)
        out_box.columnconfigure(0, weight=1)
        row += 1

        self.out_label = ttk.Label(out_box, text="尚未选择输出目录", foreground="#777")
        self.out_label.grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Button(out_box, text="选择输出目录…", command=self._pick_out_dir).grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Button(out_box, text="用默认目录（源文件旁）", command=self._use_default_out).grid(
            row=1, column=1, sticky="w", pady=(6, 0)
        )

        action = ttk.Frame(self)
        action.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        action.columnconfigure(0, weight=1)
        row += 1

        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.start_btn = ttk.Button(action, text="开始解密", command=self._start)
        self.start_btn.grid(row=0, column=1)
        self.cancel_btn = ttk.Button(
            action, text="停止", command=self._cancel, state="disabled"
        )
        self.cancel_btn.grid(row=0, column=2, padx=(6, 0))

        log_box = ttk.LabelFrame(self, text="日志", padding=4)
        log_box.grid(row=row, column=0, sticky="nsew", pady=4)
        log_box.columnconfigure(0, weight=1)
        log_box.rowconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

        self.log = tk.Text(log_box, height=10, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_box, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)
        self.log.tag_configure("ok", foreground="#0a7d2c")
        self.log.tag_configure("err", foreground="#b00020")
        self.log.tag_configure("info", foreground="#333")

    # ---------- 选择动作 ----------

    def _pick_identity(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 age identity 文件",
            filetypes=[("identity 文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.identity_file = Path(path)
        self.key_text.delete("1.0", "end")
        self.key_text.insert("1.0", "AGE-SECRET-KEY-（已从文件读取，内容不显示）")
        self._log(f"已选择私钥文件：{path}", "info")

    def _clear_key(self) -> None:
        self.key_text.delete("1.0", "end")
        self.identity_file = None
        self._log("已清空私钥输入。", "info")

    def _pick_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择要解密的 .age 文件",
            filetypes=[("age 加密文件", "*.age"), ("所有文件", "*.*")],
        )
        if paths:
            self.targets = [Path(p) for p in paths]
            self._refresh_target_label()

    def _pick_folder(self) -> None:
        folder = filedialog.askdirectory(title="选择包含 .age 文件的文件夹")
        if not folder:
            return
        # 递归收集，兼容 README 里按年份分目录的 submissions/2026/ 结构
        self.targets = sorted(Path(folder).rglob("*.age"))
        self._refresh_target_label()

    def _clear_targets(self) -> None:
        self.targets = []
        self._refresh_target_label()

    def _refresh_target_label(self) -> None:
        if not self.targets:
            self.target_label.configure(text="尚未选择", foreground="#777")
            return
        self.target_label.configure(
            text=f"已选择 {len(self.targets)} 个文件", foreground="#333"
        )

    def _pick_out_dir(self) -> None:
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.out_dir = Path(folder)
            self.out_label.configure(text=f"输出到：{folder}", foreground="#333")

    def _use_default_out(self) -> None:
        self.out_dir = None
        self.out_label.configure(
            text="输出到：每个 .age 文件同目录下的 <原名>.txt", foreground="#333"
        )

    # ---------- 解密主流程 ----------

    def _resolve_identity(self, tmp_dir: Path) -> tuple[Path | None, str | None]:
        """得到可传给 age -i 的 identity 文件路径。

        用户选文件时直接复用；粘贴文本时写入临时目录（权限受限、用完即删）。
        返回 (路径, 错误信息)，二选一为 None。
        """
        if self.identity_file is not None:
            if not self.identity_file.is_file():
                return None, f"私钥文件不存在：{self.identity_file}"
            return self.identity_file, None

        raw = self.key_text.get("1.0", "end")
        key = parse_identity_text(raw)
        if not key:
            return None, "未找到私钥：请粘贴以 AGE-SECRET-KEY- 开头的文本，或选择 identity 文件。"
        if key == "AGE-SECRET-KEY-" or "已从文件读取" in raw:
            return None, "私钥文本框是占位内容，请重新选择 identity 文件。"

        target = tmp_dir / "identity.txt"
        # 只写私钥那一行，临时文件在 finally 中删除
        target.write_text(key + "\n", encoding="utf-8")
        return target, None

    def _start(self) -> None:
        if self.age_exe is None:
            messagebox.showerror(APP_TITLE, "未找到 age.exe。请把本工具放在仓库 tools 目录下，或让 age 进入 PATH。")
            return
        if not self.targets:
            messagebox.showwarning(APP_TITLE, "请先选择要解密的 .age 文件或文件夹。")
            return
        if self.worker and self.worker.is_alive():
            return

        self.cancel_flag.clear()
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.configure(maximum=len(self.targets), value=0)
        self._log(f"开始解密，共 {len(self.targets)} 个文件。", "info")

        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def _cancel(self) -> None:
        self.cancel_flag.set()
        self._log("已请求停止，正在结束当前文件…", "info")

    def _run(self) -> None:
        import tempfile

        ok = fail = 0
        tmp_identity: Path | None = None

        try:
            with tempfile.TemporaryDirectory(prefix="age-decrypt-") as tmp:
                identity, err = self._resolve_identity(Path(tmp))
                if err:
                    self._log(err, "err")
                    return
                tmp_identity = identity
                assert identity is not None

                for index, src in enumerate(self.targets, start=1):
                    if self.cancel_flag.is_set():
                        self._log("已停止，剩余文件未处理。", "info")
                        break
                    try:
                        self._decrypt_one(identity, src)
                        ok += 1
                    except Exception as exc:  # 单个文件失败不应中断整批
                        fail += 1
                        self._log(f"[失败] {src.name}：{exc}", "err")
                    self.log_queue.put(("progress", str(index)))
        finally:
            # 粘贴来的私钥临时文件必须删除；选文件方式不产生临时文件
            if tmp_identity is not None and tmp_identity.exists():
                try:
                    tmp_identity.unlink()
                except OSError:
                    pass
            self.log_queue.put(("done", f"完成：成功 {ok} 个，失败 {fail} 个。"))

    def _decrypt_one(self, identity: Path, src: Path) -> None:
        if self.out_dir is not None:
            dest = self.out_dir / (src.stem + ".txt")
            self.out_dir.mkdir(parents=True, exist_ok=True)
        else:
            dest = src.with_suffix(".txt")

        result = subprocess.run(
            [str(self.age_exe), "-d", "-i", str(identity), str(src)],
            capture_output=True,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            if ERR_NO_MATCH in stderr:
                raise RuntimeError(ERR_NO_MATCH_HINT)
            raise RuntimeError(stderr or f"age 退出码 {result.returncode}")

        # 明文写盘。utf-8-sig 让 Windows 记事本/Excel 打开中文不乱码
        dest.write_bytes(result.stdout)
        self._log(f"[成功] {src.name} → {dest}", "ok")

    # ---------- 日志 ----------

    def _log(self, text: str, tag: str = "info") -> None:
        self.log_queue.put((tag, text))

    def _drain_log(self) -> None:
        try:
            while True:
                kind, text = self.log_queue.get_nowait()
                if kind == "progress":
                    self.progress.configure(value=int(text))
                    continue
                if kind == "done":
                    self._append(text, "info")
                    self.start_btn.configure(state="normal")
                    self.cancel_btn.configure(state="disabled")
                    continue
                self._append(text, kind)
        except queue.Empty:
            pass
        self.after(100, self._drain_log)

    def _append(self, text: str, tag: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")


def _install_crash_log() -> None:
    """把未捕获异常写到 exe 同目录的 crash.log。

    --windowed 打包后没有控制台，异常会静默丢失，导致「进程在但窗口不出现」
    这种无法排查的现象。写盘是最低成本的现场保留手段。
    """
    import traceback

    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    log_path = base / "crash.log"

    def hook(exc_type, exc_value, exc_tb) -> None:
        try:
            log_path.write_text(
                "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                encoding="utf-8",
            )
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def main() -> None:
    _install_crash_log()
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("720x680")
    root.minsize(600, 560)
    DecryptApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
