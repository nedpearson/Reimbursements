$hosts = "$env:windir\System32\drivers\etc\hosts"
$before = Get-Content $hosts
$after = $before | Where-Object { $_ -notmatch 'bridgebox\.ai' }
Set-Content -Path $hosts -Value $after -Encoding ascii
ipconfig /flushdns | Out-Null
$removed = $before.Count - $after.Count
[System.Windows.Forms.MessageBox]::Show("Removed $removed hosts line(s) for bridgebox.ai and flushed DNS. reimbursements.bridgebox.ai will now use real internet DNS.","Hosts fixed") | Out-Null
