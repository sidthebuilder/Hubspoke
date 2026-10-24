# Export the reply cache to text, stop tracking the binary cache, and commit everything else (git-ignored files,
# including .env, stay out). Output in git_commit_out.txt.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
$msg = if ($args.Count -gt 0) { $args[0] } else { "Results" }
"" | Out-File $out
& $vpy (Join-Path $here "cache_io.py") export *>> $out
git rm --cached --quiet results/cache.sqlite *>> $out
git add -A *>> $out
git status --short *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m $msg *>> $out
git log --oneline -n 3 *>> $out
git ls-files | Select-String -Pattern "\.env$" *>> $out
