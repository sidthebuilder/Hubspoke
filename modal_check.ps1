$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
& $vpy -m modal profile current *> (Join-Path $here "modal_check_log.txt")
& $vpy -m modal app list *>> (Join-Path $here "modal_check_log.txt")
"exit=$LASTEXITCODE" | Out-File -Append (Join-Path $here "modal_check_log.txt")
