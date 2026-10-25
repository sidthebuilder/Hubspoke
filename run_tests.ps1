# Run the test suite and the scripted-agent validation. Logs: tests_log.txt, validate_log.txt.
$here = $PSScriptRoot  # the repository folder
$vpy = Join-Path $here ".venv\Scripts\python.exe"
Set-Location $here
& $vpy -m pytest -q tests -p no:cacheprovider *> (Join-Path $here "tests_log.txt")
& $vpy -m hubspoke validate *> (Join-Path $here "validate_log.txt")
