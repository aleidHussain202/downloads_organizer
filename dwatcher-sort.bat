@echo off
rem One-shot sort of your Downloads folder
cd /d "%~dp0"
.venv\Scripts\python.exe -m dwatcher.cli once
pause
