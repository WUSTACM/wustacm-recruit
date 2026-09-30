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

recipient="$(awk 'NF && $1 !~ /^#/ { print $0 }' "$public_key")"
[[ "$recipient" =~ ^age1[a-z0-9]+$ ]] || fail "public-key.txt 尚未设置正式 age 公钥，请等待管理员完成配置。"

remote="$(git -C "$root" remote get-url origin 2>/dev/null)" ||
    fail "无法读取 origin。请先 Fork 仓库，再 Clone 你自己的 Fork。"
case "$remote" in
    https://github.com/*/*|git@github.com:*/*) ;;
    *) fail "origin 不是可识别的 GitHub 仓库地址。请从自己的 Fork 复制 HTTPS 地址重新 Clone。" ;;
esac
owner="$(printf '%s' "$remote" | sed -E 's#^(https://github\.com/|git@github\.com:)([^/]+)/.*#\2#')"
[[ "$owner" =~ ^[A-Za-z0-9-]+$ ]] || fail "无法识别 Fork 的 GitHub 用户名。"
github_user="$(printf '%s' "$owner" | tr '[:upper:]' '[:lower:]')"
[[ "$github_user" != "wustacm" ]] ||
    fail "当前 Clone 的是 WUSTACM 原仓库。请先 Fork，再 Clone 你自己的 Fork。"

printf 'GitHub 用户名：%s\n' "$github_user"
read -r -p '请输入用于接收面试通知的邮箱：' email ||
    fail "没有输入邮箱，请重新运行脚本。"
email="$(printf '%s' "$email" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
[[ "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]] ||
    fail "邮箱格式看起来不正确，请重新运行脚本。"

mkdir -p "$root/submissions"
output="$root/submissions/$github_user.age"

# Run a temporary copy so executable permission is not changed in the Git checkout.
temp_age="$(mktemp /tmp/wustacm-age.XXXXXX)"
trap 'rm -f "$temp_age"' EXIT
cp "$age_source" "$temp_age"
chmod 700 "$temp_age"
printf '%s\n' "$email" | "$temp_age" -R "$public_key" -o "$output" ||
    fail "加密失败，请检查 public-key.txt 并重新运行脚本。"
[[ -s "$output" ]] || fail "加密文件为空，请联系招新负责人。"

printf '\n已生成：submissions/%s.age\n' "$github_user"
printf '下一步：运行 git status，只添加上面这个 .age 文件，然后 Commit、Push 并创建 PR。\n'
