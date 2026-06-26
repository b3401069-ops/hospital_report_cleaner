@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=clean"

if not exist "src\report_cleaner\cli.py" (
    echo This batch file must be run from the hospital_report_cleaner folder.
    echo Expected file was not found: src\report_cleaner\cli.py
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
    echo Python was not found.
    echo Please install Python 3, then run this batch file again.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Using Python:
%PYTHON_CMD% -c "import sys; print(sys.executable)"
if errorlevel 1 (
    echo Python could not be started.
    pause
    exit /b 1
)

echo Checking required Python packages...
%PYTHON_CMD% -c "import pandas, openpyxl, xlrd, dateutil" >nul 2>nul
if errorlevel 1 (
    echo Required packages are missing. Installing from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Package installation failed.
        pause
        exit /b 1
    )
)

set "PYTHONPATH=%CD%\src"

echo.
echo Running hospital report cleaner command: %COMMAND%
echo.
%PYTHON_CMD% -m report_cleaner.cli %COMMAND%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Done.
) else (
    echo Failed with exit code %EXIT_CODE%.
)

pause
exit /b %EXIT_CODE%
