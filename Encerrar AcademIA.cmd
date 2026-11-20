@echo off
setlocal
if not exist "%~dp0backend\.venv\Scripts\pythonw.exe" exit /b 1
start "" "%~dp0backend\.venv\Scripts\pythonw.exe" "%~dp0scripts\academia_local.py" --stop
exit /b 0
