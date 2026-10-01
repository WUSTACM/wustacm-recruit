#!/usr/bin/env bash
set -euo pipefail

fail() {
    printf '错误：%s\n' "$1" >&2
    exit 1
}

root="$(cd "$(dirname "$0")" && pwd)"
public_key="$root/public-key.txt"

[[ "$(uname -s)" == "Darwin" ]] || fail "这个脚本适用于 macOS；Windows 请运行 submit.ps1。"
case "$(uname -m)" in
    arm64) age_source="$root/tools/darwin-arm64/age" ;;
    x86_64) age_source="$root/tools/darwin-amd64/age" ;;
    *) fail "暂不支持这台 Mac 的处理器架构：$(uname -m)" ;;
esac

[[ -f "$age_source" ]] || fail "仓库内缺少 age 程序，请重新 Clone 正式仓库。"
[[ -f "$public_key" ]] || fail "缺少 public-key.txt，请联系招新负责人。"

# 必须先剥掉可能的 UTF-8 BOM 再交给 awk：
# BOM 会让首行首个字段不等于 "#"，注释行就会被当成公钥一起输出，
# 导致下面的正则校验失败，脚本直接拒绝运行。
recipient="$(sed '1s/^\xEF\xBB\xBF//' "$public_key" | awk 'NF && $1 !~ /^#/ { print $0 }')"
[[ "$recipient" =~ ^age1[a-z0-9]+$ ]] || fail "public-key.txt 尚未设置正式 age 公钥，请等待管理员完成配置。"

# age -R 不认注释行，会报 malformed recipient。
# 上面已提取出唯一公钥，这里写进临时文件再传给 age，
# 使得 public-key.txt 带注释时脚本依然可用。
recipient_file="$(mktemp "${TMPDIR:-/tmp}/wustlaba-recipient.XXXXXX")"
printf '%s\n' "$recipient" > "$recipient_file"

remote="$(git -C "$root" remote get-url origin 2>/dev/null)" ||
    fail "无法读取 origin。请先 Fork 仓库，再 Clone 你自己的 Fork。"
case "$remote" in
    https://github.com/*/*|git@github.com:*/*) ;;
    *) fail "origin 不是可识别的 GitHub 仓库地址。请从自己的 Fork 复制 HTTPS 地址重新 Clone。" ;;
esac
owner="$(printf '%s' "$remote" | sed -E 's#^(https://github\.com/|git@github\.com:)([^/]+)/.*#\2#')"
[[ "$owner" =~ ^[A-Za-z0-9-]+$ ]] || fail "无法识别 Fork 的 GitHub 用户名。"
github_user="$(printf '%s' "$owner" | tr '[:upper:]' '[:lower:]')"
[[ "$github_user" != "wustlaba" ]] ||
    fail "当前 Clone 的是招新组原仓库。请先 Fork，再 Clone 你自己的 Fork。"

printf 'GitHub 用户名：%s\n' "$github_user"
read -r -p '请输入用于接收面试通知的邮箱：' email ||
    fail "没有输入邮箱，请重新运行脚本。"
email="$(printf '%s' "$email" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
[[ "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]] ||
    fail "邮箱格式看起来不正确，请重新运行脚本。"

# 按提交年份归档，避免 submissions 根目录随年份增长堆积
year="$(date +%Y)"
mkdir -p "$root/submissions/$year"
output="$root/submissions/$year/$github_user.age"

# Run a temporary copy so executable permission is not changed in the Git checkout.
temp_age="$(mktemp /tmp/wustlaba-age.XXXXXX)"
# 单个 trap 同时清理 age 临时副本和公钥临时文件
trap 'rm -f "$temp_age" "$recipient_file"' EXIT
cp "$age_source" "$temp_age"
chmod 700 "$temp_age"
printf '%s\n' "$email" | "$temp_age" -R "$recipient_file" -o "$output" ||
    fail "加密失败，请检查 public-key.txt 并重新运行脚本。"
[[ -s "$output" ]] || fail "加密文件为空，请联系招新负责人。"

printf '\n已生成：submissions/%s/%s.age\n' "$year" "$github_user"
printf '下一步：运行 git status，只添加上面这个 .age 文件，然后 Commit、Push 并创建 PR。\n'
