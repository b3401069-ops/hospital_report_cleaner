@echo off
chcp 65001 >nul
echo ================================================
echo   醫院報表清洗工具 - 安裝與執行
echo ================================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python！
    echo 請先安裝 Python 3.8 以上版本：
    echo https://www.python.org/downloads/
    echo.
    echo 安裝時請勾選 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/2] 安裝必要套件...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [錯誤] 套件安裝失敗！
    pause
    exit /b 1
)
echo      ✓ 套件安裝完成

echo.
echo [2/2] 執行報表清洗...
echo.

REM 確保目錄存在
if not exist "raw" mkdir raw
if not exist "output" mkdir output

python main.py

echo.
echo ================================================
echo   完成！結果在 output\cleaned_reports.xlsx
echo ================================================
pause
