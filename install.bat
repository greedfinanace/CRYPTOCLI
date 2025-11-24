@echo off
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check your python and pip installation.
    pause
    exit /b %errorlevel%
)
echo Dependencies installed successfully.
pause
