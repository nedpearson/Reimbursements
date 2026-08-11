@echo off
cd /d "%~dp0"
> _infra.txt echo === RAILWAY WHOAMI ===
railway whoami >> _infra.txt 2>&1
echo === RAILWAY LIST === >> _infra.txt
railway list >> _infra.txt 2>&1
echo === WRANGLER (Cloudflare) WHOAMI === >> _infra.txt
wrangler whoami >> _infra.txt 2>&1
echo === CF ENV TOKENS === >> _infra.txt
if defined CLOUDFLARE_API_TOKEN (echo CLOUDFLARE_API_TOKEN set) else (echo no CLOUDFLARE_API_TOKEN) >> _infra.txt
if defined CF_API_TOKEN (echo CF_API_TOKEN set) else (echo no CF_API_TOKEN) >> _infra.txt
echo === flarectl? === >> _infra.txt
where flarectl >> _infra.txt 2>&1
echo DONE >> _infra.txt
type _infra.txt
