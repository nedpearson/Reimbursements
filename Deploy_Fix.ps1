$ErrorActionPreference='Continue'
Set-Location $PSScriptRoot
"=== updating requirements.txt on nedpearson/Reimbursements main ===" | Out-File _deployfix.txt -Encoding utf8
$path='requirements.txt'
$content=[Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
$sha=(gh api repos/nedpearson/Reimbursements/contents/requirements.txt --jq '.sha')
"current sha: $sha" | Out-File _deployfix.txt -Append -Encoding utf8
gh api -X PUT repos/nedpearson/Reimbursements/contents/requirements.txt -f message="Add google-generativeai and requests (Railway deps fix)" -f content=$content -f sha=$sha -f branch=main 2>&1 | Out-File _deployfix.txt -Append -Encoding utf8
"=== DONE (exit $LASTEXITCODE) ===" | Out-File _deployfix.txt -Append -Encoding utf8
