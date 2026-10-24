# Commit only the given paths (relative to the repo). Usage: git_commit_paths.ps1 "message" path1 path2 ...
$here = "d:\we make devs\apart\hubspoke"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
$msg = $args[0]
$paths = @($args | Select-Object -Skip 1)
"" | Out-File $out
git add -- @paths *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m $msg -- @paths *>> $out
git log --oneline -n 3 *>> $out
