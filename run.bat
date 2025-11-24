@echo off
python main.py
if %errorlevel% neq 0 (
    echo Application exited with error.
    pause
)
