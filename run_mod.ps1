# Runs `python -m <module> <args>` with the project venv; console output goes to mod_<module>_<PID>_log.txt.
# Example: run_mod.ps1 hubspoke.round2 startlow startlow main
$here = $PSScriptRoot  # the repository folder
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$env:HUBSPOKE_OFFLINE = "1"  # analysis only: never call a model
$cli = @($args)
$name = if ($cli.Count -gt 0) { $cli[0] } else { "none" }
$log = Join-Path $here "mod_${name}_${PID}_log.txt"
"$(Get-Date -Format s) start: $($cli -join ' ')" | Out-File -Append -Encoding utf8 $log
& $vpy -m @cli *>> $log
"$(Get-Date -Format s) exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
