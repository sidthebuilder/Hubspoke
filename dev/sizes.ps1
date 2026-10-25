# Dev helper: sizes of the cache files and the largest tracked files (GitHub rejects files over 100 MB).
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$out = Join-Path $here "sizes_out.txt"
Set-Location $here
Get-ChildItem results -Filter "cache*" | Select-Object Name, @{n="MB"; e={[math]::Round($_.Length / 1MB, 1)}} | Format-Table -AutoSize | Out-File -Width 200 -Encoding utf8 $out
"largest files under results:" | Out-File -Append -Encoding utf8 $out
Get-ChildItem results -Recurse -File | Sort-Object Length -Descending | Select-Object -First 8 FullName, @{n="MB"; e={[math]::Round($_.Length / 1MB, 1)}} | Format-Table -AutoSize | Out-File -Append -Width 250 -Encoding utf8 $out
