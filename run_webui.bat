@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title ComfyUI API WebUI 啟動器
color 0A

cd /d "%~dp0"

echo ===================================================
echo   正在啟動 ComfyUI API 系統 (前後端整合版)
echo ===================================================
echo.

REM --- 設定連接埠 ---
set "FRONTEND_PORT=15005"
set "BACKEND_PORT=15006"

echo [資訊] 前端預定埠口: http://127.0.0.1:%FRONTEND_PORT%
echo [資訊] 後端預定埠口: http://127.0.0.1:%BACKEND_PORT%
echo.

REM --- 檢查後端虛擬環境 ---
if not exist ".venv\Scripts\activate.bat" (
    echo [錯誤] 找不到 Python 虛擬環境 (.venv)。
    echo 請先在根目錄執行 python -m venv .venv 並安裝 requirements.txt
    pause
    exit /b 1
)

REM --- 檢查前端依賴性 ---
if not exist "frontend\node_modules" (
    echo [警告] 偵測到前端尚未安裝依賴套件 (node_modules)...
    echo [資訊] 正在自動執行 npm install，這可能需要一點時間...
    cd frontend
    call npm install
    cd ..
    echo [資訊] 前端依賴套件安裝完成。
    echo.
)

REM --- 啟動後端服務 (在新的獨立視窗中) ---
echo [步驟 1/2] 正在獨立視窗啟動 Python 後端服務 (port:%BACKEND_PORT%)...
start "ComfyUI API Backend" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python -m app.server --port %BACKEND_PORT% --reload"

REM --- 啟動前端服務 (在當前視窗中) ---
echo [步驟 2/2] 正在當前視窗啟動 Vue/Vite 前端服務 (port:%FRONTEND_PORT%)...
cd frontend

REM 設定環境變數供 Vite 讀取
set "PORT=%FRONTEND_PORT%"
set "BACKEND_PORT=%BACKEND_PORT%"

REM 執行前端開發伺服器
call npm run dev -- --port %FRONTEND_PORT%

cd ..
