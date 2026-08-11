@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "Deploy_Fix.ps1"
type _deployfix.txt
