param([string]$Gpu = "H100:1")
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "deploy_all_log.txt"
Set-Location $here
$env:HUBSPOKE_GPU = $Gpu
"$(Get-Date -Format s) deploy start gpu=$Gpu" | Out-File -Append $log
& $vpy (Join-Path $here "modal_deploy.py") *>> $log
"$(Get-Date -Format s) deploy done exit=$LASTEXITCODE" | Out-File -Append $log
