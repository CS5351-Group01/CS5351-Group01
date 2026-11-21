# 一键搭环境：建虚拟环境 → 装依赖 → 跑测试
#
# 用法（在仓库根目录，或者任意位置都行）：
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#
# 为什么要这个脚本：
#   · 手动敲 / 粘贴多行命令，经常被聊天软件吃掉换行，两行粘成一行就报错
#   · `activate` 会被 PowerShell 执行策略拦住
#   · 这里全部用绝对路径调 python，两步都绕开了

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

Write-Host ""
Write-Host "仓库目录: $repoRoot" -ForegroundColor Cyan

# ---------------------------------------------------------------- 1. Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "找不到 python。先装 Python 3.10 或更高版本，装的时候记得勾 Add to PATH。" -ForegroundColor Red
    exit 1
}
$version = & python --version 2>&1
Write-Host "1/4 Python: $version"

# ---------------------------------------------------------------- 2. venv
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "2/4 虚拟环境已存在，跳过创建"
} else {
    Write-Host "2/4 创建虚拟环境（约 10 秒）…"
    & python -m venv .venv
    if (-not (Test-Path $venvPython)) {
        Write-Host "虚拟环境创建失败，检查上面 python -m venv 的报错。" -ForegroundColor Red
        exit 1
    }
}

# ---------------------------------------------------------------- 3. 依赖
Write-Host "3/4 安装依赖…"
$installed = $false
try {
    & $venvPython -m pip install -q --disable-pip-version-check -r requirements.txt
    $installed = ($LASTEXITCODE -eq 0)
} catch {
    $installed = $false
}

if (-not $installed) {
    Write-Host "   官方源失败，换清华镜像重试…" -ForegroundColor Yellow
    & $venvPython -m pip install -q --disable-pip-version-check `
        -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    $installed = ($LASTEXITCODE -eq 0)
}

if (-not $installed) {
    Write-Host "依赖装不上。多半是网络——换手机热点，或者挂了 VPN 的话先关掉再试。" -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------- 4. 测试
Write-Host "4/4 跑测试…"
Write-Host ""
& $venvPython -m pytest tests -q
$code = $LASTEXITCODE

Write-Host ""
if ($code -eq 0) {
    Write-Host "环境好了。以后跑测试用这条：" -ForegroundColor Green
    Write-Host "  .\.venv\Scripts\python.exe -m pytest tests -q" -ForegroundColor Green
} else {
    Write-Host "测试没全过。把上面的输出截图发群里。" -ForegroundColor Red
}
exit $code
