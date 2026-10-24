$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "modal_check_log.txt"
Set-Location $here
$env:COLUMNS = "250"
$env:PYTHONIOENCODING = "utf-8"
"$(Get-Date -Format s)" | Out-File -Encoding utf8 $log
& $vpy -m modal app list *>> $log
& $vpy -m modal container list *>> $log
"exit=$LASTEXITCODE" | Out-File -Append $log
