@echo off
rem One click: bundle the full packet and open a ready-to-send email.
cd /d "%~dp0"
where pythonw >nul 2>nul && ( start "" pythonw "email_packet.py" & exit /b )
where python  >nul 2>nul && ( start "" python  "email_packet.py" & exit /b )
where py      >nul 2>nul && ( start "" py      "email_packet.py" & exit /b )
echo Python not found. Run Start.bat once first.
pause
