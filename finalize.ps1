# Wait for the Llama replication and the live replay to finish, then build every result and verify it.
# Writes finalize_log.txt. Safe to run more than once.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "finalize_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
function Say($m) { "$(Get-Date -Format s) $m" | Out-File -Append -Encoding utf8 $log }
Say "start"
for ($i = 0; $i -lt 120; $i++) {
    $nl = (Get-ChildItem (Join-Path $here "results\main_llama") -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count
    $nr = (Get-ChildItem (Join-Path $here "results\livereplay") -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count
    if ($nl -ge 84 -and $nr -ge 24) { break }
    if ($i % 4 -eq 0) { Say "waiting: llama $nl/84, livereplay $nr/24" }
    Start-Sleep -Seconds 30
}
Say "runs complete"
& $vpy -m hubspoke analyse --src main *>> $log
& $vpy -m hubspoke.explore main *>> $log
& $vpy (Join-Path $here "report\results_auto.py") main *>> $log
& $vpy -m hubspoke analyse --src main_llama *>> $log
& $vpy -m hubspoke.explore main_llama *>> $log
& $vpy (Join-Path $here "report\results_auto.py") main_llama *>> $log
& $vpy (Join-Path $here "report\make_prompt_appendix.py") *>> $log
Say "analysis done"
& $vpy -m hubspoke verify --src main *>> $log
Say "verify main exit=$LASTEXITCODE"
& $vpy -m hubspoke verify --src main_llama *>> $log
Say "verify main_llama exit=$LASTEXITCODE"
& $vpy -m pytest -q tests -p no:cacheprovider *>> $log
Say "tests exit=$LASTEXITCODE"
Say "done"
