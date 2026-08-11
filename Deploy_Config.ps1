$ErrorActionPreference='Continue'
Set-Location $PSScriptRoot
$path='config.json'
$content=[Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
$sha=(gh api repos/nedpearson/Reimbursements/contents/config.json --jq '.sha')
"sha: $sha" | Out-File _cfgpush.txt -Encoding utf8
gh api -X PUT repos/nedpearson/Reimbursements/contents/config.json -f message="Add share_token so the /share public link works" -f content=$content -f sha=$sha -f branch=main 2>&1 | Out-File _cfgpush.txt -Append -Encoding utf8
"DONE $LASTEXITCODE" | Out-File _cfgpush.txt -Append -Encoding utf8
