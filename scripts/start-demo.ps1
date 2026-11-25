# 一键启动演示：起服务 + 等就绪 + 打开浏览器
#
# 用法：双击本文件，或者在仓库根目录跑
#   powershell -ExecutionPolicy Bypass -File scripts\start-demo.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

Write-Host ""
Write-Host "仓库目录: $repoRoot" -ForegroundColor Cyan

# ---------------------------------------------------------------- 环境检查
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "还没建虚拟环境。先跑一次：" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1"
    Read-Host "按回车退出"
    exit 1
}

# ---------------------------------------------------------------- 端口检查
$listening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "服务已经在跑了（8000 端口被占），直接开浏览器。" -ForegroundColor Yellow
} else {
    Write-Host "启动服务…（会弹一个新窗口，别关它）" -ForegroundColor Cyan
    Start-Process -FilePath $venvPython -ArgumentList "run.py" -WorkingDirectory $repoRoot

    $up = $false
    foreach ($i in 1..40) {
        Start-Sleep -Milliseconds 700
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $up = $true; break }
        } catch {}
    }

    if (-not $up) {
        Write-Host "服务没起来。看那个新开的窗口里报了什么错。" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }
}

# ---------------------------------------------------------------- 开浏览器
Start-Process "http://127.0.0.1:8000"
Write-Host ""
Write-Host "已打开 http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "服务在另一个窗口里跑着，演示期间别关它。"
Write-Host ""
Write-Host "第一次用的话，先注册一个账号再上传文件。" -ForegroundColor DarkGray
