@echo off
setlocal
set "ACADEMIA_PYTHON=%~dp0backend\.venv\Scripts\pythonw.exe"
if not exist "%ACADEMIA_PYTHON%" (
  echo O ambiente Python do projeto ainda nao esta instalado.
  echo Consulte docs\instalacao\iniciar-com-dois-cliques.md.
  pause
  exit /b 1
)
start "" "%ACADEMIA_PYTHON%" "%~dp0scripts\academia_local.py"
exit /b 0
