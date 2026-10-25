# Rebuild every table, figure and check from the stored run files and the reply cache, in order. Offline: no model
# is called (HUBSPOKE_OFFLINE=1, so a missing reply is an error). Windows PowerShell; each step is one python
# command that runs the same on any OS (see README). Log: finalize_log.txt. Safe to run more than once.
$here = $PSScriptRoot  # the repository folder
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "finalize_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$env:HUBSPOKE_OFFLINE = "1"
"$(Get-Date -Format s) start" | Out-File -Encoding utf8 $log
function Step($label, [string[]]$cmd) {
    & $vpy @cmd *>> $log
    "$(Get-Date -Format s) $label exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
}
function Count($folder) { (Get-ChildItem (Join-Path $here "results\$folder") -Filter "*-s*.json" -ErrorAction SilentlyContinue).Count }
function Has($folder) { (Count $folder) -gt 0 }

Step "tests" @("-m", "pytest", "-q", "tests", "-p", "no:cacheprovider")
Step "validate (scripted agents)" @("-m", "hubspoke", "validate")
foreach ($src in @("main", "main_llama", "main_gptoss")) {        # registered H1-H4 per model, complete runs only
    if ((Count $src) -lt 84) { "$(Get-Date -Format s) skip $src ($(Count $src) of 84 runs)" | Out-File -Append -Encoding utf8 $log; continue }
    if (Has $src) {
        Step "analyse $src" @("-m", "hubspoke", "analyse", "--src", $src)
        Step "explore $src" @("-m", "hubspoke.explore", $src)
        Step "tables $src" @("report\results_auto.py", $src)
        Step "hub check $src" @("-m", "hubspoke.round2", "hub", $src)
    }
}
if (Has "startlow") { Step "start-low qwen (R2.3)" @("-m", "hubspoke.round2", "startlow", "startlow", "main") }
if (Has "startlow_llama") { Step "start-low llama (R2.3)" @("-m", "hubspoke.round2", "startlow", "startlow_llama", "main_llama") }
foreach ($f in @("canary2", "canary2_llama", "canary2_gptoss")) {  # R2.1, complete folders only
    if ((Count $f) -ge 12) { Step "canary v2 $f" @("-m", "hubspoke.round2", "canary2", $f) }
}
Step "judge validation (R2.2)" @("-m", "hubspoke.round2", "judge")
Step "robustness (exploratory)" @("-m", "hubspoke.robust")
Step "round-2 figures" @("-m", "hubspoke.figs2")
foreach ($f in @("canary2", "canary2_llama", "canary2_gptoss")) {  # the audit tool, run on our own canary trials
    if ((Count $f) -ge 12) {
        foreach ($arm in @("shared", "shared_rule", "shared_tags", "private")) {
            Step "audit demo $f $arm" @("-m", "hubspoke.audit", "--demo", "--demo-folder", $f, "--demo-arm", $arm)
        }
    }
}
Step "main tables, every model" @("report\table_models.py")
Step "prompt appendix" @("report\make_prompt_appendix.py")
Step "predictions appendix" @("report\predictions_table.py")
$need = @{ "main" = 84; "main_llama" = 84; "main_gptoss" = 84; "startlow" = 60; "startlow_llama" = 60;
           "canary2" = 12; "canary2_llama" = 12; "canary2_gptoss" = 12 }
foreach ($src in $need.Keys) {  # complete folders only (verify prints outcomes)
    if ((Count $src) -ge $need[$src]) { Step "verify $src" @("-m", "hubspoke", "verify", "--src", $src) }
}
Step "verify judge" @("-m", "hubspoke", "verify", "--src", "judge")
"$(Get-Date -Format s) done" | Out-File -Append -Encoding utf8 $log
