@echo off
title CinemaPredict - Digital Cinema Delivery Intelligence
echo ===================================================================
echo  CinemaPredict - Digital Cinema Delivery Intelligence
echo  AI-Powered Predictive Optimization (College PBL Project)
echo ===================================================================

cd /d "%~dp0"

set PY_EXE="C:\Users\Kavinraj\AppData\Local\Programs\Python\Python313\python.exe"

if exist %PY_EXE% (
    echo [INFO] Using Python 3.13 at %PY_EXE%
    %PY_EXE% run.py
) else (
    echo [INFO] Python 3.13 specific path not found, trying system python...
    python run.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application failed to launch.
    echo Please make sure the dependencies are installed:
    echo pip install -r requirements.txt
    echo.
    pause
)
