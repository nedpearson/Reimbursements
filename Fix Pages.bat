@echo off
cd /d "%~dp0"
echo === gh version === > _pages_result.txt
gh --version >> _pages_result.txt 2>&1
echo === auth status === >> _pages_result.txt
gh auth status >> _pages_result.txt 2>&1
echo === POST enable pages (main /docs) === >> _pages_result.txt
gh api -X POST repos/nedpearson/Reimbursements/pages -f "source[branch]=main" -f "source[path]=/docs" >> _pages_result.txt 2>&1
echo === PUT set source (main /docs) === >> _pages_result.txt
gh api -X PUT repos/nedpearson/Reimbursements/pages -f "source[branch]=main" -f "source[path]=/docs" >> _pages_result.txt 2>&1
echo === GET current pages config === >> _pages_result.txt
gh api repos/nedpearson/Reimbursements/pages >> _pages_result.txt 2>&1
echo DONE >> _pages_result.txt
type _pages_result.txt
