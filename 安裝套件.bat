@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

if not exist "requirements.txt" (
    echo 這個批次檔必須放在 hospital_report_cleaner 專案資料夾內執行。
    echo 找不到必要檔案：requirements.txt
    pause
    exit /b 1
)

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo 找不到 Python。
    echo 請先安裝 Python 3，再重新執行這個檔案。
    echo 下載網址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 使用的 Python：
%PYTHON_CMD% -c "import sys; print(sys.executable)"
if errorlevel 1 (
    echo Python 無法啟動。
    pause
    exit /b 1
)

echo.
echo 正在安裝或更新必要套件...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo 套件安裝失敗。
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src"

echo.
echo 正在檢查執行環境...
%PYTHON_CMD% -m report_cleaner.cli check-env
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo 安裝與環境檢查完成。
) else (
    echo 套件已安裝，但環境檢查仍有錯誤。
)

pause
exit /b %EXIT_CODE%
