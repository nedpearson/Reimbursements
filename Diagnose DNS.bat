@echo off
cd /d "%~dp0"
> _dns.txt echo === default resolver ===
nslookup reimbursements.bridgebox.ai >> _dns.txt 2>&1
echo. >> _dns.txt
echo === via Cloudflare 1.1.1.1 === >> _dns.txt
nslookup reimbursements.bridgebox.ai 1.1.1.1 >> _dns.txt 2>&1
echo. >> _dns.txt
echo === via Google 8.8.8.8 === >> _dns.txt
nslookup reimbursements.bridgebox.ai 8.8.8.8 >> _dns.txt 2>&1
echo. >> _dns.txt
echo === current DNS servers === >> _dns.txt
ipconfig /all | findstr /i "DNS Servers" >> _dns.txt 2>&1
echo DONE >> _dns.txt
type _dns.txt
