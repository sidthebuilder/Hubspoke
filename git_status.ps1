# Dev helper: repository status into git_check.txt (changed, untracked, last commits), UTF-8.
$here = $PSScriptRoot
$out = Join-Path $here "git_check.txt"
Set-Location $here
"$(Get-Date -Format s)" | Out-File -Encoding utf8 $out
git status --short 2>&1 | Out-File -Append -Encoding utf8 $out
"--- last commits" | Out-File -Append -Encoding utf8 $out
git log --oneline -n 5 2>&1 | Out-File -Append -Encoding utf8 $out
