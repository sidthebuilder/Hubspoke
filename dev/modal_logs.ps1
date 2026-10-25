# Stream one Modal app's logs to a file (stop the process after a short while). Usage: modal_logs.ps1 <app-name>
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$vpy = Join-Path $here ".venv\Scripts\python.exe"
$app = $args[0]
$log = Join-Path $here "modal_logs_$app.txt"
Set-Location $here
$env:COLUMNS = "250"
$env:PYTHONIOENCODING = "utf-8"
& $vpy -m modal app logs $app *> $log
