@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=clean"

if not exist "src\report_cleaner\cli.py" (
    echo 這個批次檔必須放在 hospital_report_cleaner 專案資料夾內執行。
    echo 找不到必要檔案：src\report_cleaner\cli.py
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
    echo 請先安裝 Python 3，再重新執行這個批次檔。
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

if /I not "%COMMAND%"=="check-env" (
    echo 正在檢查必要的 Python 套件...
    %PYTHON_CMD% -c "import pandas, openpyxl, xlrd, dateutil" >nul 2>nul
    if errorlevel 1 (
        echo 缺少必要套件，正在依 requirements.txt 安裝...
        %PYTHON_CMD% -m pip install -r requirements.txt
        if errorlevel 1 (
            echo 套件安裝失敗。
            pause
            exit /b 1
        )
    )
)

set "PYTHONPATH=%CD%\src"

set "COMMAND_LABEL=%COMMAND%"
if /I "%COMMAND%"=="clean" set "COMMAND_LABEL=清洗報表"
if /I "%COMMAND%"=="export-mapping-review" set "COMMAND_LABEL=匯出待確認規則"
if /I "%COMMAND%"=="apply-mapping-review" set "COMMAND_LABEL=套用確認規則"
if /I "%COMMAND%"=="check-env" set "COMMAND_LABEL=檢查環境"
if /I "%COMMAND%"=="case-manager" set "COMMAND_LABEL=個管報表"

echo.
echo 正在執行：%COMMAND_LABEL%
echo.
%PYTHON_CMD% -m report_cleaner.cli %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo 執行完成。
) else (
    echo 執行失敗，錯誤代碼：%EXIT_CODE%。
)

pause
exit /b %EXIT_CODE%
