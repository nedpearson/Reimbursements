@echo off
cd /d "%~dp0"
where git >nul 2>nul || ( echo Git not found. Install from https://git-scm.com then re-run. & pause & exit /b )
if not exist ".git" (
  git init
  git branch -M main
  git remote add origin https://github.com/nedpearson/Reimbursements.git
)
git config user.name "Ned Pearson"
git config user.email "nedpearson@gmail.com"
if exist "_to_delete" rmdir /s /q "_to_delete"
git add -A
git commit -m "Reimbursement Manager + live drill-down portal"
git push -u origin main
echo.
echo ============================================================
echo  Done. If no errors above, everything is on GitHub:
echo    https://github.com/nedpearson/Reimbursements
echo  Next: enable GitHub Pages (Settings - Pages - main - /docs)
echo ============================================================
pause
