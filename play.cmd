@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run_game.py %*
) else (
  python run_game.py %*
)
if errorlevel 1 pause
