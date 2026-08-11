@echo off
cd /d "%~dp0"
> _repos.txt echo === gh auth status ===
gh auth status >> _repos.txt 2>&1
echo === repos (name / visibility / updated) === >> _repos.txt
gh repo list nedpearson --limit 200 >> _repos.txt 2>&1
echo === which repos have server.py at root === >> _repos.txt
for /f "delims=" %%r in ('gh repo list nedpearson --limit 200 --json nameWithOwner -q ".[].nameWithOwner" 2^>nul') do gh api repos/%%r/contents/server.py --jq ".path" >nul 2>&1 && echo HAS server.py: %%r >> _repos.txt
echo DONE >> _repos.txt
type _repos.txt
