# Dev helper: regenerate the predictions appendix, run the tests and the secret scan, stop tracking the report drafts
# (they stay on disk), and commit. Output in git_commit_out.txt.
$here = Split-Path -Parent $PSScriptRoot
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
"" | Out-File -Encoding utf8 $out
& $vpy (Join-Path $here "report\predictions_table.py") *>> $out
& $vpy -m pytest -q tests -p no:cacheprovider *>> $out
"pytest exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $out
if ($LASTEXITCODE -ne 0) { "STOP: tests failed" | Out-File -Append -Encoding utf8 $out; exit 1 }
& $vpy (Join-Path $here "dev\secret_scan.py")
Get-Content (Join-Path $here "secret_scan_out.txt") | Out-File -Append -Encoding utf8 $out
foreach ($f in @("draft.md", "abstract_draft.md", "notes_for_writing.md", "notes_round2.md", "appendix_ai_use.md", "appendix_limits.md")) {
    git rm --cached --quiet --ignore-unmatch "report/$f" *>> $out
}
git add -A *>> $out
git status --short *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m "Neutral wording on who wrote entries (registered content unchanged, change logged); report drafts kept local, not in the repository" *>> $out
git log --oneline -n 3 *>> $out
