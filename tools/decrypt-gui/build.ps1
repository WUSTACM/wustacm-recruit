# age 解密 GUI 打包脚本
#
# 用法：在仓库根目录执行
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\decrypt-gui\build.ps1
#
# 产物：tools\decrypt-gui\dist\age-decrypt-gui.exe（单文件、无控制台窗口）

param(
    # 跳过 PyInstaller 安装检查，用于离线重复构建
    [switch] $SkipInstall
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path $PSScriptRoot 'decrypt_gui.py'
$icon = Join-Path $PSScriptRoot 'icon.ico'

if (-not (Test-Path -LiteralPath $py -PathType Leaf)) {
    throw "缺少 decrypt_gui.py：$py"
}

if (-not $SkipInstall) {
    # PyInstaller 不在标准库内，先确认可用再构建，避免构建到一半才报错
    $hasPyInstaller = $false
    try {
        python -m PyInstaller --version *> $null
        $hasPyInstaller = ($LASTEXITCODE -eq 0)
    } catch {
        $hasPyInstaller = $false
    }

    if (-not $hasPyInstaller) {
        Write-Host '未检测到 PyInstaller，正在安装…'
        python -m pip install --upgrade pyinstaller
        if ($LASTEXITCODE -ne 0) {
            throw 'PyInstaller 安装失败，请检查网络或改用 --SkipInstall 手动准备环境。'
        }
    }
}

$args = @(
    '--noconfirm',
    '--clean',
    '--onefile',
    '--windowed',              # GUI 程序，不弹控制台窗口
    '--name', 'age-decrypt-gui',
    # PyInstaller 的静态分析会漏掉部分标准库模块，漏掉时 exe 启动即
    # ModuleNotFoundError，而 --windowed 会把异常吞掉，表现为「进程在、
    # 窗口不出现」，极难排查，因此在这里显式声明。
    '--hidden-import', 'queue',
    '--hidden-import', 'tkinter',
    '--hidden-import', 'tkinter.ttk',
    '--hidden-import', 'tkinter.filedialog',
    '--hidden-import', 'tkinter.messagebox',
    '--hidden-import', 'tempfile',
    '--hidden-import', 'subprocess',
    '--distpath', (Join-Path $PSScriptRoot 'dist'),
    '--workpath', (Join-Path $PSScriptRoot 'build'),
    '--specpath', $PSScriptRoot
)

# 图标是可选的：缺失时不阻断构建，只是 exe 用默认图标
if (Test-Path -LiteralPath $icon -PathType Leaf) {
    $args += @('--icon', $icon)
} else {
    Write-Host '提示：未找到 icon.ico，将使用默认图标。'
}

$args += $py

Write-Host "开始构建：python -m PyInstaller $($args -join ' ')"
python -m PyInstaller @args
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller 构建失败，请查看上方输出。'
}

$exe = Join-Path $PSScriptRoot 'dist\age-decrypt-gui.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw "构建结束但未找到产物：$exe"
}

$sizeMB = [math]::Round((Get-Item -LiteralPath $exe).Length / 1MB, 2)
Write-Host ''
Write-Host "构建成功：$exe（$sizeMB MB）"

# 冒烟验证：启动 exe，确认进程活着且没有写出 crash.log。
# 只检查「文件生成」不足以证明可用——曾出现过程序能打包、能运行，但缺
# 模块导致窗口从未创建的情况，因此这里做一次真实启动检查。
Write-Host '正在验证 exe 可启动…'
$crashLog = Join-Path $PSScriptRoot 'dist\crash.log'
Remove-Item -LiteralPath $crashLog -ErrorAction SilentlyContinue

$proc = Start-Process -FilePath $exe -PassThru
Start-Sleep -Seconds 8
$ok = -not $proc.HasExited
if (-not $ok) {
    Write-Host "警告：exe 启动后已退出（退出码 $($proc.ExitCode)）。" -ForegroundColor Red
} elseif (Test-Path -LiteralPath $crashLog) {
    Write-Host '警告：exe 运行时报错，crash.log 内容如下：' -ForegroundColor Red
    Get-Content -LiteralPath $crashLog -Raw
    $ok = $false
} else {
    Write-Host 'exe 冒烟验证通过：进程存活且无崩溃日志。'
}

if (-not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    # 等文件锁释放，否则下次构建覆盖 exe 会 PermissionError
    Start-Sleep -Seconds 2
}

Write-Host '提示：此 exe 需与仓库中的 tools\windows-amd64\age.exe 配合使用，或让 age 进入 PATH。'
if (-not $ok) {
    throw '构建产物未通过启动验证，请检查上方输出。'
}
