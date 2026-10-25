# Unattended chain for the rest of round 2 (R2.4): the gpt-oss main run, canary v2 on its aged_sharedmem runs, the
# judge on those notes, every round-2 analysis, and the offline rebuild checks. Log: chain_gptoss_log.txt
# Resumable: finished runs are skipped and every stored reply is reused from the cache, so running this script
# again after an interruption continues where it stopped.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "chain_gptoss_log.txt"
$cfg = Join-Path $here "configs\modal_gptoss120b.json"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
function Note($msg) { "$(Get-Date -Format s) $msg" | Out-File -Append -Encoding utf8 $log }
function Runs($folder) { (Get-ChildItem (Join-Path $here "results\$folder") -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count }

Note "chain start"
for ($i = 1; ($i -le 3) -and ((Runs "main_gptoss") -lt 84); $i++) {
    Note "gpt-oss main run, pass $i ($(Runs 'main_gptoss') of 84 run files on disk)"
    & $vpy -m hubspoke run --config $cfg --T 40 --out main_gptoss --workers 84 --start history --reasoning --blind *>> $log
}
Note "main_gptoss: $(Runs 'main_gptoss') of 84 run files"
if ((Runs "main_gptoss") -lt 84) { Note "STOP: main run incomplete"; exit 1 }
for ($i = 1; ($i -le 2) -and ((Runs "canary2_gptoss") -lt 12); $i++) {
    Note "canary v2 on gpt-oss, pass $i"
    & $vpy -m hubspoke canary2 --config $cfg --workers 12 --src main_gptoss --out canary2_gptoss *>> $log
}
Note "canary2_gptoss: $(Runs 'canary2_gptoss') of 12 files; judge (Qwen, as registered)"
& $vpy -m hubspoke judge --folders canary2_gptoss --workers 16 *>> $log
Note "round-2 analyses"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "round2_all.ps1")
foreach ($src in @("main_gptoss", "canary2_gptoss", "judge")) {
    Note "verify $src"
    & $vpy -m hubspoke verify --src $src *>> $log
    Note "verify $src exit=$LASTEXITCODE"
}
Note "chain done"
