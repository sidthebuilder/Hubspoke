# Deploy gpt-oss-120b as a third Modal app; its URL goes to .env as HUBSPOKE_BASE_URL_GPTOSS.
$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$log = Join-Path $here "deploy_all_log.txt"
Set-Location $here
$env:HUBSPOKE_GPU = "H100:1"
$env:HUBSPOKE_MODEL = "openai/gpt-oss-120b"
$env:HUBSPOKE_REVISION = "b5c939de8f754692c1647ca79fbf85e8c1e70f8a"
$env:HUBSPOKE_SERVED = "hubspoke-gptoss120b"
$env:HUBSPOKE_APP = "hubspoke-vllm-gptoss"
$env:HUBSPOKE_MAXLEN = "16384"
"$(Get-Date -Format s) deploy gptoss start" | Out-File -Append $log
& $vpy (Join-Path $here "modal_deploy.py") HUBSPOKE_BASE_URL_GPTOSS *>> $log
"$(Get-Date -Format s) deploy gptoss done exit=$LASTEXITCODE" | Out-File -Append $log
