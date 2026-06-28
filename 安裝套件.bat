@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

if not exist "requirements.txt" (
    echo This batch file must be run from the hospital_report_cleaner folder.
    echo Expected file was not found: requirements.txt
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
    echo Please install Python 3 first, then run this file again.
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

echo.
echo Installing or updating required packages...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Package installation failed.
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src"

echo.
echo Running environment check...
%PYTHON_CMD% -m report_cleaner.cli check-env
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Setup completed.
) else (
    echo Setup finished, but the environment check still has errors.
)

pause
exit /b %EXIT_CODE%
