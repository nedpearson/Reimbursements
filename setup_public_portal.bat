@echo off
rem Publishes docs\ to a small PUBLIC repo so the live link works on GitHub's free plan.
rem The main Reimbursements repo (code + data) STAYS PRIVATE.
cd /d "%~dp0"
set "HAVEGH=1"
where gh >nul 2>nul || set "HAVEGH="
if defined HAVEGH (
  gh auth status >nul 2>nul || set "HAVEGH="
)
if defined HAVEGH (
  gh repo view nedpearson/reimbursement-portal >nul 2>nul || gh repo create nedpearson/reimbursement-portal --public --description "Expense reimbursement portal"
) else (
  echo NOTE: GitHub CLI not available. If the public repo does not exist yet, create it once
  echo at https://github.com/new  - name: reimbursement-portal, PUBLIC, no README -
  echo then run this again. Enable Pages at Settings - Pages - main - / root.
)
set "PUB=%~dp0..\reimbursement-portal-pub"
if not exist "%PUB%\.git" git clone https://github.com/nedpearson/reimbursement-portal.git "%PUB%" || ( echo RESULT: CLONE_FAILED - does the public repo exist yet? & exit /b 1 )
robocopy docs "%PUB%" /MIR /XD .git >nul
type nul > "%PUB%\.nojekyll"
cd /d "%PUB%"
git add -A
git commit -m "portal update" >nul 2>nul
git branch -M main
git push -u origin main
if defined HAVEGH gh api -X POST repos/nedpearson/reimbursement-portal/pages -f "source[branch]=main" -f "source[path]=/" >nul 2>nul
echo RESULT: PORTAL_PUBLISHED - https://nedpearson.github.io/reimbursement-portal/
