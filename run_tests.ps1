$here = "d:\we make devs\apart\hubspoke"
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
& $vpy -m pytest -q tests *> (Join-Path $here "tests_log.txt")
& $vpy -m hubspoke validate *> (Join-Path $here "validate_log.txt")
