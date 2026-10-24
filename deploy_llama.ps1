# Deploy the replication model as a second Modal app; its URL goes to .env as HUBSPOKE_BASE_URL_LLAMA.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "deploy_all_log.txt"
Set-Location $here
$env:HUBSPOKE_GPU = "H100:1"
$env:HUBSPOKE_MODEL = "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4"
$env:HUBSPOKE_REVISION = "2123003760781134cfc31124aa6560a45b491fdf"
$env:HUBSPOKE_SERVED = "hubspoke-llama70b"
$env:HUBSPOKE_APP = "hubspoke-vllm-llama"
"$(Get-Date -Format s) deploy llama start" | Out-File -Append $log
& $vpy (Join-Path $here "modal_deploy.py") HUBSPOKE_BASE_URL_LLAMA *>> $log
"$(Get-Date -Format s) deploy llama done exit=$LASTEXITCODE" | Out-File -Append $log
