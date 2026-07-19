@echo off
cd /d "%~dp0"
echo Rebuilding the web portal from current data...
where python >nul 2>nul && ( python build_portal.py ) || ( py build_portal.py )
echo.
echo Publishing to GitHub (nedpearson/Reimbursements)...
git add -A
git commit -m "Update reimbursement portal"
git push
echo.
echo Done. Live link: https://nedpearson.github.io/Reimbursements/
pause
