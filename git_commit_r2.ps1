$here = "d:\we make devs\apart\hubspoke"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
"" | Out-File $out
git add -- PREREGISTRATION.md *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m "Register round 2 (canary v2, judge validation, start-low, gpt-oss replication, AI Village field check) before any run" -- PREREGISTRATION.md *>> $out
git log --oneline -n 2 *>> $out
