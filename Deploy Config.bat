@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "Deploy_Config.ps1"
type _cfgpush.txt
