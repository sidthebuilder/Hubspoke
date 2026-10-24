param([string]$Message = "Pre-registration: code and plan before any LLM data")
$here = "d:\we make devs\apart\hubspoke"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
if (-not (Test-Path (Join-Path $here ".git"))) { git init -b main *> $out }
git add -A *>> $out
git -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m $Message *>> $out
git log --oneline -n 3 *>> $out
git status --short *>> $out
git ls-files *>> $out
