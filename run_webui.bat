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

REM =====================================================
REM  Auto-detect ComfyUI Server Port
REM =====================================================
echo [Auto-Detect] Scanning for ComfyUI Server...
echo.

set "_COMFY_PORT="
for %%P in (8188 8080 18080 8189 8190 18888 28188) do (
    if not defined _COMFY_PORT (
        for /f %%A in ('curl -s -o nul -w "%%{http_code}" --connect-timeout 2 http://127.0.0.1:%%P/system_stats 2^>nul') do (
            if "%%A"=="200" (
                set "_COMFY_PORT=%%P"
                echo   [OK] Found ComfyUI on port %%P
            )
        )
    )
)

if not defined _COMFY_PORT (
    echo   [!!] No running ComfyUI server found.
    echo        Checked: 8188, 8080, 18080, 8189, 8190, 18888, 28188
    echo        Falling back to default port 8188
    set "_COMFY_PORT=8188"
)

REM =====================================================
REM  Set all ports automatically
REM =====================================================
set "COMFYUI_API_URL=http://127.0.0.1:!_COMFY_PORT!"
set "FRONTEND_PORT=15005"
set "BACKEND_PORT=15006"

echo.
echo  -----------------------------------------
echo    ComfyUI   : !COMFYUI_API_URL!
echo    Frontend  : http://127.0.0.1:!FRONTEND_PORT!
echo    Backend   : http://127.0.0.1:!BACKEND_PORT!
echo  -----------------------------------------
echo.

REM =====================================================
REM  Check virtual environment
REM =====================================================
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found. Run: python -m venv .venv
    pause
    exit /b 1
)

REM =====================================================
REM  Check frontend dependencies
REM =====================================================
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

REM =====================================================
REM  Export env vars out of setlocal scope
REM =====================================================
set "ROOT_DIR=%~dp0"
set "VENV_ACT=%ROOT_DIR%.venv\Scripts\activate.bat"

endlocal & (
    set "COMFYUI_API_URL=%COMFYUI_API_URL%"
    set "FRONTEND_PORT=%FRONTEND_PORT%"
    set "BACKEND_PORT=%BACKEND_PORT%"
    set "ROOT_DIR=%ROOT_DIR%"
    set "VENV_ACT=%VENV_ACT%"
)
cd /d "%~dp0"

REM =====================================================
REM  Launch Backend + Frontend in same terminal
REM =====================================================
echo Launching Backend + Frontend in same terminal...
echo Press CTRL+C to stop all servers.
echo.

REM --- Start backend in background (same window, no new terminal) ---
echo [1/2] Starting backend (port:%BACKEND_PORT%)...
start /b cmd /c "call "%VENV_ACT%" && python -m app.server --port %BACKEND_PORT%"

REM --- Wait for backend to initialize ---
echo [INFO] Waiting 3s for backend...
timeout /t 3 /nobreak >nul

REM --- Start frontend in foreground (same window) ---
echo [2/2] Starting frontend (port:%FRONTEND_PORT%)...
cd frontend
set "PORT=%FRONTEND_PORT%"
call npm run dev -- --port %FRONTEND_PORT%

cd ..
echo.
echo [INFO] Frontend stopped. Cleaning up backend...

REM --- Kill any lingering backend process on our port ---
for /f "tokens=5" %%P in ('netstat -aon ^| findstr ":%BACKEND_PORT% " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /f /pid %%P >nul 2>&1
)

echo [INFO] All servers stopped.
pause
