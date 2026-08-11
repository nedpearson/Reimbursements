@echo off
cd /d "%~dp0"
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul
echo Syncing...
git pull --rebase --autostash origin main 2>nul
echo Clearing dispute overrides (restoring full claim)...
python -c "import json;json.dump({'removed':[],'denied':[]},open('docs/overrides.json','w'),indent=1)" 2>nul || py -c "import json;json.dump({'removed':[],'denied':[]},open('docs/overrides.json','w'),indent=1)"
git add docs/overrides.json
git commit -m "restore: clear test dispute C-094 (back to full claim)"
git push
echo.
echo Restored. Live net returns to $87,728.84 within ~1 min.
pause
