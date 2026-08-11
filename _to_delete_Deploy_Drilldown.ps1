$ErrorActionPreference = "Stop"
Set-Location "C:\dev\github\personal\Reimbursements"

function Push-File($repoPath, $localPath, $message) {
  Write-Host "Pushing $repoPath ..."
  $shaJson = gh api "repos/nedpearson/Reimbursements/contents/$repoPath`?ref=main" 2>$null | ConvertFrom-Json
  $sha = $shaJson.sha
  $bytes = [System.IO.File]::ReadAllBytes($localPath)
  $b64 = [Convert]::ToBase64String($bytes)
  $tmpJson = New-TemporaryFile
  $payload = @{
    message = $message
    content = $b64
    sha     = $sha
    branch  = "main"
  } | ConvertTo-Json -Compress
  Set-Content -Path $tmpJson -Value $payload -Encoding utf8NoBOM
  gh api "repos/nedpearson/Reimbursements/contents/$repoPath" -X PUT --input $tmpJson | Out-Null
  Remove-Item $tmpJson -Force
  Write-Host "Done: $repoPath"
}

Push-File "docs/index.html" "docs\index.html" "Portal: QuickBooks-style drill-down on category rows in stat detail modal"
Push-File "portal_template.html" "portal_template.html" "Portal: QuickBooks-style drill-down on category rows in stat detail modal"

Write-Host ""
Write-Host "=== DEPLOY COMPLETE ==="
