# One-time local setup for hubspoke (Windows PowerShell). Creates .venv inside this folder.
$ErrorActionPreference = "Continue"
$here = "d:\we make devs\apart\hubspoke"
$py = "C:\Users\SHASHANK KUMAR\AppData\Local\Programs\Python\Python311\python.exe"
$log = Join-Path $here "setup_log.txt"
"start $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
if (-not (Test-Path (Join-Path $here ".venv\Scripts\python.exe"))) {
    & $py -m venv (Join-Path $here ".venv") *>> $log
}
$vpy = Join-Path $here ".venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip *>> $log
& $vpy -m pip install numpy scipy pandas matplotlib pytest modal *>> $log
& $vpy -c "import numpy, scipy, pandas, matplotlib, pytest, modal; print('imports ok')" *>> $log
& git --version *>> $log
"done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 $log
