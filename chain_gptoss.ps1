# Unattended chain for the rest of round 2 (R2.4): wait for the gpt-oss main run, then canary v2 on its aged_sharedmem
# runs, the judge on those notes, every round-2 analysis, and the offline rebuild checks. Log: chain_gptoss_log.txt
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "chain_gptoss_log.txt"
$cfg = Join-Path $here "configs\modal_gptoss120b.json"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
function Note($msg) { "$(Get-Date -Format s) $msg" | Out-File -Append -Encoding utf8 $log }
function Runs($folder) { (Get-ChildItem (Join-Path $here "results\$folder") -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count }

Note "chain start; waiting for results\main_gptoss to finish"
$deadline = (Get-Date).AddHours(8)
while ((Get-Date) -lt $deadline) {
    $rl = Join-Path $here "results\main_gptoss\run_log.txt"
    if ((Test-Path $rl) -and (Select-String -Path $rl -Pattern "finished; client stats" -Quiet)) { break }
    Start-Sleep -Seconds 60
}
Note "main_gptoss: $(Runs 'main_gptoss') run files"
if ((Runs "main_gptoss") -lt 84) {  # resumable: only missing runs are played
    Note "re-running missing gpt-oss runs"
    & $vpy -m hubspoke run --config $cfg --T 40 --out main_gptoss --workers 84 --start history --reasoning --blind *>> $log
    Note "main_gptoss now: $(Runs 'main_gptoss') run files"
}
Note "canary v2 on gpt-oss"
& $vpy -m hubspoke canary2 --config $cfg --workers 12 --src main_gptoss --out canary2_gptoss *>> $log
Note "canary2_gptoss: $(Runs 'canary2_gptoss') files; judge (Qwen, as registered)"
& $vpy -m hubspoke judge --folders canary2_gptoss --workers 16 *>> $log
Note "round-2 analyses"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "round2_all.ps1")
foreach ($src in @("main_gptoss", "startlow", "startlow_llama", "canary2", "canary2_llama", "canary2_gptoss", "judge")) {
    Note "verify $src"
    & $vpy -m hubspoke verify --src $src *>> $log
    Note "verify $src exit=$LASTEXITCODE"
}
Note "chain done"
