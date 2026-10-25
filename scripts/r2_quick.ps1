# Canary v2 tables, judge validation, robustness and figures (no start-low, no gpt-oss). Log: r2_quick_log.txt
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "r2_quick_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$env:HUBSPOKE_OFFLINE = "1"
"$(Get-Date -Format s) start" | Out-File -Encoding utf8 $log
foreach ($f in @("canary2", "canary2_llama", "canary2_gptoss")) {
    if (Test-Path "results\$f") { & $vpy -m hubspoke.round2 canary2 $f *>> $log; "canary2 $f exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log }
}
& $vpy -m hubspoke.round2 judge *>> $log; "judge exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke.robust *>> $log; "robust exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke.figs2 *>> $log; "figs2 exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
"$(Get-Date -Format s) done" | Out-File -Append -Encoding utf8 $log
