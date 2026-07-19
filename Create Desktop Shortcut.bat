@echo off
cd /d "%~dp0"
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Reimbursement Manager.lnk'); $lnk.TargetPath = '%~dp0Start.bat'; $lnk.WorkingDirectory = '%~dp0'; $lnk.IconLocation = '%~dp0assets\icon.ico'; $lnk.Description = 'Reimbursement Manager'; $lnk.Save()"
echo Desktop shortcut "Reimbursement Manager" created.
pause
