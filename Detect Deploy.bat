@echo off
cd /d "%~dp0"
set OUT=_deploy_info.txt
> %OUT% echo ==== RAILWAY CLI ====
railway --version >> %OUT% 2>&1
railway status >> %OUT% 2>&1
echo ==== railway config files here ==== >> %OUT%
dir /a /b .railway railway.json railway.toml nixpacks.toml Procfile 2>> %OUT%
echo ==== GH CLI ==== >> %OUT%
gh --version >> %OUT% 2>&1
gh auth status >> %OUT% 2>&1
echo ==== GH REPOS ==== >> %OUT%
gh repo list nedpearson --limit 100 >> %OUT% 2>&1
echo ==== GIT REMOTE (this folder) ==== >> %OUT%
git remote -v >> %OUT% 2>&1
echo DONE >> %OUT%
type %OUT%
