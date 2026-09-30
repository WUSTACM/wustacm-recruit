param(
    [string] $Email
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$ageExe = Join-Path $root 'tools\windows-amd64\age.exe'
$publicKey = Join-Path $root 'public-key.txt'
# 按提交年份归档，避免 submissions 根目录随年份增长堆积
$year = (Get-Date).Year
$submissions = Join-Path $root (Join-Path 'submissions' $year)

if (-not (Test-Path -LiteralPath $ageExe -PathType Leaf)) {
    throw '仓库内缺少 tools/windows-amd64/age.exe，请重新 Clone 正式仓库。'
}

if (-not (Test-Path -LiteralPath $publicKey -PathType Leaf)) {
    throw '缺少 public-key.txt，请联系招新负责人。'
}

$recipients = @(Get-Content -LiteralPath $publicKey | Where-Object {
    $line = $_.Trim()
    $line.Length -gt 0 -and -not $line.StartsWith('#')
})
if ($recipients.Count -ne 1 -or $recipients[0].Trim() -notmatch '^age1[a-z0-9]+$') {
    throw 'public-key.txt 尚未设置正式 age 公钥，请等待管理员完成配置。'
}

$remote = & git -C $root remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remote)) {
    throw '无法读取 origin。请先 Fork 仓库，再 Clone 你自己的 Fork。'
}
$remote = ([string] $remote).Trim()
$remoteMatch = [regex]::Match($remote, '^(?:https://github\.com/|git@github\.com:)(?<owner>[A-Za-z0-9-]+)/[A-Za-z0-9_.-]+/?$')
if (-not $remoteMatch.Success) {
    throw 'origin 不是可识别的 GitHub 仓库地址。请从自己的 Fork 复制 HTTPS 地址重新 Clone。'
}
$githubUser = $remoteMatch.Groups['owner'].Value.ToLowerInvariant()
if ($githubUser -eq 'wustlaba') {
    throw '当前 Clone 的是招新组原仓库。请先 Fork，再 Clone 你自己的 Fork。'
}

if ([string]::IsNullOrWhiteSpace($Email)) {
    Write-Host "GitHub 用户名：$githubUser"
    $Email = Read-Host '请输入用于接收面试通知的邮箱'
}
if ($null -eq $Email) {
    throw '没有输入邮箱，请重新运行脚本。'
}
$Email = $Email.Trim()
if ($Email -notmatch '^[^\s@]+@[^\s@]+\.[^\s@]+$') {
    throw '邮箱格式看起来不正确，请重新运行脚本。'
}

if (-not (Test-Path -LiteralPath $submissions -PathType Container)) {
    New-Item -ItemType Directory -Path $submissions | Out-Null
}
$output = Join-Path $submissions ($githubUser + '.age')

# Email is passed to age through stdin; no plaintext file is created.
$Email | & $ageExe -R $publicKey -o $output
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output -PathType Leaf)) {
    throw '加密失败，请检查 public-key.txt 并重新运行脚本。'
}
if ((Get-Item -LiteralPath $output).Length -eq 0) {
    throw '加密文件为空，请联系招新负责人。'
}

Write-Host ''
Write-Host ('已生成：submissions/' + $year + '/' + $githubUser + '.age')
Write-Host '下一步：运行 git status，只添加上面这个 .age 文件，然后 Commit、Push 并创建 PR。'
