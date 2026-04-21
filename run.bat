@echo off
REM CinePredict - Movie Success Prediction System
REM Simple setup and run script for Windows
REM Uses 'py' launcher for maximum compatibility

echo.
echo ████████████████████████████████████████████████████████████████████████
echo   CINEPREDICT - Movie Success Prediction System
echo   Setting up environment and launching pipeline...
echo ████████████████████████████████████████████████████████████████████████
echo.

REM Try to find Python using py launcher first (most reliable on Windows)
py --version >nul 2>&1
if errorlevel 0 (
    REM Using py launcher
    echo Found Python using 'py' launcher
    py -m pip install pandas numpy scikit-learn matplotlib seaborn pillow -q 2>nul
    py main.py
    pause
    exit /b 0
)

REM Fallback to python3
python3 --version >nul 2>&1
if errorlevel 0 (
    echo Found Python using 'python3' command
    python3 -m pip install pandas numpy scikit-learn matplotlib seaborn pillow -q 2>nul
    python3 main.py
    pause
    exit /b 0
)

REM If all else fails
echo.
echo ERROR: Python was not found on your system
echo.
echo Solutions:
echo 1. Install Python from https://www.python.org/
echo 2. Or use: python3 run.py
echo 3. Or use: py run.py
echo.
pause
exit /b 1
