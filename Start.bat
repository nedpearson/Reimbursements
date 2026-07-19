@echo off
cd /d "%~dp0"
where python >nul 2>nul || where py >nul 2>nul || (
  echo Python not found. Install from https://www.python.org/downloads/
  echo During install, tick "Add Python to PATH", then run this again.
  pause & exit /b
)
if not exist ".deps_installed" (
  echo First run - installing components, this takes a minute...
  where python >nul 2>nul && ( python -m pip install -q -r requirements.txt && echo ok> .deps_installed )
  if not exist ".deps_installed" ( py -m pip install -q -r requirements.txt && echo ok> .deps_installed )
)
where pythonw >nul 2>nul && ( start "" pythonw "app.pyw" & exit )
where py >nul 2>nul && ( start "" py -w "app.pyw" & exit )
