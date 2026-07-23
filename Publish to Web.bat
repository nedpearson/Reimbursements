@echo off
cd /d "%~dp0"

rem --- SAFETY: tag the current published state as a restore point BEFORE changing anything ---
rem If the wrong thing gets published, "Undo Last Publish.bat" rolls back to this point.
for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do set STAMP=%%c%%a%%b-%%d%%e
git rev-parse HEAD >nul 2>nul && git tag -f "restore-point" >nul 2>nul
git rev-parse HEAD >nul 2>nul && git tag "pub-%STAMP%" >nul 2>nul

echo Rebuilding the web portal from current data...
where python >nul 2>nul && ( python build_portal.py ) || ( py build_portal.py )
echo.
echo Publishing to GitHub (nedpearson/Reimbursements)...
git add -A
git commit -m "Update reimbursement portal"
git push
git push --tags 2>nul
echo.
echo Done. Live link: https://nedpearson.github.io/Reimbursements/
echo A restore point was saved. If you ever publish something wrong, run "Undo Last Publish.bat".
echo (If the link shows 404: repo Settings - Pages - Deploy from branch - main - /docs - Save. One time only.)
pause
