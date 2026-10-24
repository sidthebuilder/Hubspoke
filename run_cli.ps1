param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
# Runs `python -m hubspoke <args>` with the project venv; console output goes to cli_<command>_log.txt.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$name = if ($CliArgs.Count -gt 0) { $CliArgs[0] } else { "none" }
$log = Join-Path $here "cli_${name}_log.txt"
"$(Get-Date -Format s) start: $($CliArgs -join ' ')" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke @CliArgs *>> $log
"$(Get-Date -Format s) exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
