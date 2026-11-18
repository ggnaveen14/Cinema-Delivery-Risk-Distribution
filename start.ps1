Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " CinemaPredict - Digital Cinema Delivery Intelligence (PBL) " -ForegroundColor Yellow
Write-Host "===================================================================" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$specificPython = "C:\Users\Kavinraj\AppData\Local\Programs\Python\Python313\python.exe"

if (Test-Path $specificPython) {
    Write-Host "[INFO] Starting with Python 3.13: $specificPython" -ForegroundColor Green
    & $specificPython run.py
} else {
    Write-Host "[INFO] Trying default python from PATH..." -ForegroundColor Yellow
    python run.py
}
