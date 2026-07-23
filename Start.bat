@echo off
cd /d "%~dp0"
rem Launch the app under the SAME Python that actually works, using its windowed
rem sibling (pythonw) so no console stays open. This bypasses the broken Microsoft
rem Store "pythonw" alias that silently does nothing on machines with multiple Pythons.

rem 1) make sure a real python exists
where python >nul 2>nul || where py >nul 2>nul || (
  echo Python not found. Install from https://www.python.org/downloads/
  echo During install tick "Add Python to PATH", then run this again.
  pause & exit /b
)

rem 2) first run: install the components the app needs (into whichever python resolves)
if not exist ".deps_installed" (
  echo First run - installing components, this takes a minute...
  python -m pip install -q -r requirements.txt >nul 2>nul || py -m pip install -q -r requirements.txt >nul 2>nul
  echo ok> .deps_installed
)

rem 3) start the app detached, no console: find pythonw next to the working python
python -c "import os,sys,subprocess;e=os.path.join(os.path.dirname(sys.executable),'pythonw.exe');e=e if os.path.exists(e) else sys.executable;subprocess.Popen([e,'app.pyw'])" && exit
py -c "import os,sys,subprocess;e=os.path.join(os.path.dirname(sys.executable),'pythonw.exe');e=e if os.path.exists(e) else sys.executable;subprocess.Popen([e,'app.pyw'])" && exit

rem 4) fallback if the above failed
start "" pyw "app.pyw" 2>nul || start "" pythonw "app.pyw"
exit
