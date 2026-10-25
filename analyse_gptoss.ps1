# The registered analysis of the gpt-oss replication (R2.4), once its 84 runs are on disk. Offline. Log: analyse_gptoss_log.txt
$here = $PSScriptRoot
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "analyse_gptoss_log.txt"
Set-Location $here
$env:PYTHONIOENCODING = "utf-8"
$env:HUBSPOKE_OFFLINE = "1"
$n = (Get-ChildItem (Join-Path $here "results\main_gptoss") -Filter "*-s*.json").Count
"$(Get-Date -Format s) start; $n run files" | Out-File -Encoding utf8 $log
if ($n -lt 84) { "STOP: incomplete" | Out-File -Append -Encoding utf8 $log; exit 1 }
& $vpy -m hubspoke analyse --src main_gptoss *>> $log
"analyse exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke.round2 hub main_gptoss *>> $log
"hub exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
& $vpy -m hubspoke.explore main_gptoss *>> $log
"explore exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
& $vpy (Join-Path $here "report\results_auto.py") main_gptoss *>> $log
"tables exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
"$(Get-Date -Format s) done" | Out-File -Append -Encoding utf8 $log
