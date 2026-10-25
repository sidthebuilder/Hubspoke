# Rebuild every round-2 table and figure from the result files (offline; no model calls). Log: round2_all_log.txt
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "round2_all_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$env:HUBSPOKE_OFFLINE = "1"
"$(Get-Date -Format s) start" | Out-File -Encoding utf8 $log
function Step($label, [string[]]$cmd) {
    "$(Get-Date -Format s) $label" | Out-File -Append -Encoding utf8 $log
    & $vpy @cmd *>> $log
    "  exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
}
if (Test-Path "results\startlow") { Step "startlow qwen" @("-m", "hubspoke.round2", "startlow", "startlow", "main") }
if (Test-Path "results\startlow_llama") { Step "startlow llama" @("-m", "hubspoke.round2", "startlow", "startlow_llama", "main_llama") }
foreach ($f in @("canary2", "canary2_llama", "canary2_gptoss")) {
    if (Test-Path "results\$f") { Step "canary2 $f" @("-m", "hubspoke.round2", "canary2", $f) }
}
Step "judge validation" @("-m", "hubspoke.round2", "judge")
foreach ($f in @("main", "main_llama", "main_gptoss")) {
    if (Test-Path "results\$f") { Step "hub check $f" @("-m", "hubspoke.round2", "hub", $f) }
}
if ((Get-ChildItem "results\main_gptoss" -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count -ge 84) {
    Step "analyse main_gptoss" @("-m", "hubspoke", "analyse", "--src", "main_gptoss")
    Step "explore main_gptoss" @("-m", "hubspoke.explore", "main_gptoss")
    Step "tables main_gptoss" @("report\results_auto.py", "main_gptoss")
}
Step "robust" @("-m", "hubspoke.robust")
Step "figures" @("-m", "hubspoke.figs2")
"$(Get-Date -Format s) done" | Out-File -Append -Encoding utf8 $log
