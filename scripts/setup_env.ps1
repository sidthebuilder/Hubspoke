# One-time local setup for hubspoke (Windows PowerShell). Creates .venv in the repository folder and installs the
# pinned requirements. Needs Python 3.11 on PATH.
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$py = "python"  # Python 3.11 on PATH
$log = Join-Path $here "setup_log.txt"
"start $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
if (-not (Test-Path (Join-Path $here ".venv\Scripts\python.exe"))) {
    & $py -m venv (Join-Path $here ".venv") *>> $log
}
$vpy = Join-Path $here ".venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip *>> $log
& $vpy -m pip install -r (Join-Path $here "requirements.txt") *>> $log
& $vpy -c "import numpy, scipy, pandas, matplotlib, pytest, modal; print('imports ok')" *>> $log
& git --version *>> $log
"done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 $log
