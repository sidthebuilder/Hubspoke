# After all runs: analysis, result tables, prompt appendix, offline verification. Logs to postprocess_log.txt.
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "postprocess_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$src = if ($args.Count -gt 0) { $args[0] } else { "main" }
"$(Get-Date -Format s) analyse $src" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke analyse --src $src *>> $log
"$(Get-Date -Format s) tables" | Out-File -Append -Encoding utf8 $log
& $vpy (Join-Path $here "report\results_auto.py") $src *>> $log
if ($src -eq "main") {
    & $vpy (Join-Path $here "report\make_prompt_appendix.py") *>> $log
}
"$(Get-Date -Format s) verify $src" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke verify --src $src *>> $log
"$(Get-Date -Format s) done exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
