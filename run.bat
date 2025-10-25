@echo off
REM Quick start script for Fire Detection System
REM Windows batch file

echo ========================================
echo ESP32-CAM Fire Detection System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Run setup first: python setup.py
    echo.
    pause
    exit /b
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if config exists
if not exist "config.json" (
    echo Config file not found!
    echo Run setup first: python setup.py
    echo.
    pause
    exit /b
)

echo.
echo Starting fire detection...
echo Press Ctrl+C to stop
echo.

REM Run fire detection
python fire_detection.py

pause
