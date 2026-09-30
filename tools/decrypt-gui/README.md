# age 解密 GUI（管理员用）

给招新负责人用来解密 `submissions/` 下新生提交的 `.age` 文件。Windows 图形界面，支持单文件或整个文件夹批量解密。

## 前提

需要两样东西：

1. **私钥**：生成 `public-key.txt` 里那把公钥时产出的 `identity` 文件（或那行 `AGE-SECRET-KEY-...` 文本）。
2. **`age.exe`**：仓库已自带 `tools/windows-amd64/age.exe`，无需另外安装。

> 私钥不匹配时解密会失败并提示「该文件不是用这把私钥加密的」。age 没有找回机制，公钥也无法反推私钥——**私钥丢了就只能换新密钥并让新生重新提交**。

## 方式一：直接运行源码（无需构建）

仓库根目录执行：

```powershell
python .\tools\decrypt-gui\decrypt_gui.py
```

只依赖 Python 标准库（tkinter 随 Python 一同安装），无需 pip 安装任何东西。

## 方式二：构建 exe

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\decrypt-gui\build.ps1
```

产物：`tools\decrypt-gui\dist\age-decrypt-gui.exe`（单文件，约 8–10 MB）。

脚本会在缺少 PyInstaller 时自动 `pip install`；离线环境可先自行安装，再加 `-SkipInstall` 跳过检查。

## 使用步骤

1. **私钥**：把 `AGE-SECRET-KEY-...` 粘进文本框（可以整段粘贴 identity 文件内容），或点「从文件读取 identity…」选择文件。
2. **待解密文件**：点「选择 .age 文件…」选单个/多个文件，或点「选择文件夹…」递归收集目录下所有 `.age`。
3. **输出**：可选自定义输出目录，或「用默认目录（源文件旁）」输出为 `<原名>.txt`。
4. 点「开始解密」。日志逐条显示成功/失败原因，可随时「停止」。

## 安全说明

- 粘贴进文本框的私钥**只存在于内存**：解密时写入系统临时目录、结束后立即删除，不会留在仓库或桌面。
- 「从文件读取 identity…」方式不产生任何临时副本，直接以该文件作为 `age -i` 参数。
- 解出的明文默认写在 `.age` 同目录的 `.txt` 里。这批文件含新生真实邮箱，**不要 commit、不要 push**——仓库 `.gitignore` 已忽略 `*identity*.txt` 与私钥行，但明文输出仍需自行确认不在版本控制内。
- exe 不做代码签名，Windows SmartScreen 可能提示「未知发布者」，选择「仍要运行」即可；也可直接跑源码方式。

## 为什么调用 age.exe 而不是 Python 库

仓库里的 `age.exe` 与新生加密时用的是同一实现，能保证行为完全一致；同时打包后没有额外的二进制依赖，也不需要在离线机器上装 `pyage` 之类的绑定。
