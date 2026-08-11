@echo off
echo Flushing Windows DNS cache...
ipconfig /flushdns
ipconfig /registerdns >nul 2>&1
echo.
echo Done. Now FULLY close Chrome (every window) and reopen it,
echo then go to https://reimbursements.bridgebox.ai
pause
