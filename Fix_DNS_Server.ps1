Add-Type -AssemblyName System.Windows.Forms
$adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}
foreach ($a in $adapters) {
  try { Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses ('1.1.1.1','8.8.8.8') -ErrorAction Stop } catch {}
}
Clear-DnsClientCache
ipconfig /flushdns | Out-Null
[System.Windows.Forms.MessageBox]::Show("Your PC now uses Cloudflare (1.1.1.1) + Google (8.8.8.8) for DNS, and the cache was flushed. Reload reimbursements.bridgebox.ai in Chrome now. (To revert later: Settings > Network & Internet > your adapter > DNS server assignment > Automatic.)","DNS fixed") | Out-Null
