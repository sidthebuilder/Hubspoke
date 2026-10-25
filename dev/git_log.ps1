# Dev helper: commit history with times (IST) into git_log_out.txt, and the size of what git tracks.
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$out = Join-Path $here "git_log_out.txt"
Set-Location $here
git log --reverse --date=format-local:"%Y-%m-%d %H:%M" --format="%h %ad %s" 2>&1 | Out-File -Encoding utf8 $out
"--- tracked size (MB)" | Out-File -Append -Encoding utf8 $out
$sum = 0; git ls-files | ForEach-Object { if (Test-Path $_) { $sum += (Get-Item $_).Length } }
[math]::Round($sum / 1MB, 1) | Out-File -Append -Encoding utf8 $out
git count-objects -vH 2>&1 | Out-File -Append -Encoding utf8 $out
