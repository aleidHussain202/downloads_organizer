@echo off
rem Continuous watch of your Downloads folder (Ctrl+C to stop)
cd /d "%~dp0"
.venv\Scripts\python.exe -m dwatcher.cli watch
pause
