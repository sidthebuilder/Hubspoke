# Dev helper: export the code at one commit into a folder outside the repository (no change to .git).
# Usage: export_commit.ps1 <commit> <target folder>
$here = Split-Path -Parent $PSScriptRoot
Set-Location $here
$commit = $args[0]
$target = $args[1]
$zip = "$target.zip"
git archive --format=zip -o $zip $commit 2>&1 | Out-File -Encoding utf8 (Join-Path $here "export_commit_out.txt")
Expand-Archive -Path $zip -DestinationPath $target -Force
Remove-Item $zip
"exported $commit to $target" | Out-File -Append -Encoding utf8 (Join-Path $here "export_commit_out.txt")
