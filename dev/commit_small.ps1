# Dev helper: commit README and hand-check instruction fixes. Output in git_commit_out.txt.
$here = Split-Path -Parent $PSScriptRoot
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
"" | Out-File -Encoding utf8 $out
git add README.md report/HANDCHECK_INSTRUCTIONS.md dev/commit_small.ps1 2>&1 | Out-File -Append -Encoding utf8 $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m "README and hand-check instructions: drop references to files no longer in the repository" 2>&1 | Out-File -Append -Encoding utf8 $out
git status --short 2>&1 | Out-File -Append -Encoding utf8 $out
git log --oneline -n 2 2>&1 | Out-File -Append -Encoding utf8 $out
