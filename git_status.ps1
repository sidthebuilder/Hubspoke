# Dev helper: repository status into git_check.txt (changed, untracked, last commits).
$here = "d:\we make devs\apart\hubspoke"
$out = Join-Path $here "git_check.txt"
Set-Location $here
"$(Get-Date -Format s)" | Out-File -Encoding utf8 $out
git status --short *>> $out
"--- last commits" | Out-File -Append -Encoding utf8 $out
git log --oneline -n 5 *>> $out
