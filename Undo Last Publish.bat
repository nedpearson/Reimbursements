@echo off
cd /d "%~dp0"
echo(
echo  UNDO LAST PUBLISH
echo  =================
echo  This rolls the shared web page back to the state it was in BEFORE your
echo  most recent Publish (the "restore-point" saved automatically each time).
echo  Your local data files are NOT changed - use the app's Archive tab for that.
echo(
git rev-parse restore-point >nul 2>nul || ( echo  No restore point found yet. Publish once first. & pause & exit /b )
set /p OK=  Type YES to roll the live page back to the last restore point:
if /I not "%OK%"=="YES" ( echo  Cancelled. & pause & exit /b )
echo(
echo  Rolling back...
git reset --hard restore-point
git push --force
echo(
echo  Done. The live page is back to the previous published version.
echo  (It may take a minute to refresh. Run Publish again when you're ready to push new changes.)
pause
