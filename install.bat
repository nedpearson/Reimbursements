@echo off
cd /d "%~dp0"
echo Installing Python dependencies...
where python >nul 2>nul && ( python -m pip install -r requirements.txt ) || ( py -m pip install -r requirements.txt )
call "Create Desktop Shortcut.bat"
