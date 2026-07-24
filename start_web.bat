@echo off
echo Starting Divorce Ledger Reimbursements Web Server...
cd /d "%~dp0"
where python >nul 2>nul && ( python server.py ) || ( py server.py )
pause
