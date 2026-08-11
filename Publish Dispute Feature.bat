@echo off
cd /d "%~dp0"
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul
echo Syncing any online updates...
git pull --rebase --autostash origin main 2>nul
echo Committing dispute docs...
git add docs/index.html docs/overrides.json portal_template.html build_portal.py config.json .github DISPUTES.md dispute-api "Publish to Web.bat"
git commit -m "Dispute feature docs (GitHub-native); mark Vercel setup superseded"
git push
echo.
echo Done. Live: https://nedpearson.github.io/Reimbursements/
pause
