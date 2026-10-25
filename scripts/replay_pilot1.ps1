# Replay pilot 1 offline with the code it was run with (commit 5e15448); writes results/verify_pilot.txt.
# The code is exported with `git archive` into a temporary folder (no change to .git) and removed afterwards.
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$commit = "5e15448"
$tmp = Join-Path $env:TEMP "hubspoke_$commit"
Set-Location $here
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
git archive --format=zip -o "$tmp.zip" $commit
Expand-Archive -Path "$tmp.zip" -DestinationPath $tmp -Force
Remove-Item "$tmp.zip"
& $vpy (Join-Path $here "scripts\replay_at_commit.py") $tmp pilot $commit
$code = $LASTEXITCODE
Remove-Item -Recurse -Force $tmp
exit $code
