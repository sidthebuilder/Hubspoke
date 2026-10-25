# Export the reply cache to text, check that no secret is in any file git would commit, and commit everything else
# (git-ignored files, including .env and the binary cache, stay out). Output in git_commit_out.txt.
$here = $PSScriptRoot  # the repository folder
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
$msg = if ($args.Count -gt 0) { $args[0] } else { "Results" }
"" | Out-File $out
& $vpy (Join-Path $here "cache_io.py") export *>> $out
& $vpy (Join-Path $here "cache_io.py") check *>> $out
if ($LASTEXITCODE -ne 0) { "STOP: the cache export does not match the database; nothing committed" | Out-File -Append $out; exit 1 }
& $vpy (Join-Path $here "secret_scan.py")
$scan = Get-Content (Join-Path $here "secret_scan_out.txt")
$scan | Out-File -Append $out
if (-not ($scan -match "^hits: 0$")) { "STOP: secret_scan found a secret; nothing committed" | Out-File -Append $out; exit 1 }
git rm --cached --quiet --ignore-unmatch results/cache.sqlite *>> $out
git add -A *>> $out
git status --short *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m $msg *>> $out
git log --oneline -n 3 *>> $out
git ls-files | Select-String -Pattern "\.env$" *>> $out
