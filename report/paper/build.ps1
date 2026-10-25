# Build the report PDF: figures from results/, then two pdflatex passes. Log: report/paper/build_log.txt
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path (Split-Path -Parent (Split-Path -Parent $here)) '.venv\Scripts\python.exe'
$log = Join-Path $here 'build_log.txt'
Push-Location $here
"build $(Get-Date -Format s)" | Out-File -Encoding utf8 $log
& $py (Join-Path $here 'make_figures.py') *>> $log
pdflatex -interaction=nonstopmode -halt-on-error main.tex *> (Join-Path $here 'pass1.txt')
pdflatex -interaction=nonstopmode -halt-on-error main.tex *> (Join-Path $here 'pass2.txt')
"pdflatex exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
Select-String -Path main.log -Pattern '^!|Overfull|Undefined|undefined|Warning' | ForEach-Object { $_.Line } | Out-File -Append -Encoding utf8 $log
"END" | Out-File -Append -Encoding utf8 $log
Pop-Location
