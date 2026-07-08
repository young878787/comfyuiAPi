@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title ComfyUI API WebUI
color 0A

cd /d "%~dp0"

echo ===================================================
echo   Starting ComfyUI API System
echo ===================================================
echo.

REM --- Port settings ---
set "FRONTEND_PORT=15005"
set "BACKEND_PORT=15006"

echo [INFO] Frontend: http://127.0.0.1:%FRONTEND_PORT%
echo [INFO] Backend:  http://127.0.0.1:%BACKEND_PORT%
echo.

REM --- Check virtual environment ---
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found. Run: python -m venv .venv
    pause
    exit /b 1
)

REM --- Check frontend dependencies ---
if not exist "frontend\node_modules" (
    echo [WARN] node_modules not found, running npm install...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    cd ..
    echo [INFO] npm install done.
    echo.
)

REM --- Save root dir ---
set "ROOT_DIR=%~dp0"
set "VENV_ACT=%ROOT_DIR%.venv\Scripts\activate.bat"

REM --- Start backend in new window ---
echo [1/2] Starting backend (port:%BACKEND_PORT%)...
start "ComfyUI API Backend" cmd /k "cd /d %ROOT_DIR% && call %VENV_ACT% && python -m app.server --port %BACKEND_PORT% --reload"

REM --- Wait for backend to initialize ---
echo [INFO] Waiting 3s for backend...
timeout /t 3 /nobreak >nul

REM --- Start frontend in current window ---
echo [2/2] Starting frontend (port:%FRONTEND_PORT%)...
cd frontend
set "PORT=%FRONTEND_PORT%"
call npm run dev -- --port %FRONTEND_PORT%

cd ..
echo.
echo [INFO] Frontend stopped.
pause
