# Runs `python -m hubspoke <args>` with the project venv; console output goes to cli_<command>_log.txt.
# No param() block on purpose: PowerShell would try to bind flags such as --out to its own common parameters.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$cli = @($args)
$name = if ($cli.Count -gt 0) { $cli[0] } else { "none" }
$log = Join-Path $here "cli_${name}_log.txt"
"$(Get-Date -Format s) start: $($cli -join ' ')" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke @cli *>> $log
"$(Get-Date -Format s) exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
