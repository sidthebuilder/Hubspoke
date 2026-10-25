# Commit the given paths (relative to the repo). Usage: git_commit_paths.ps1 "message" path1 path2 ...
# Staging uses the normal line-ending rules (text is stored with LF); the commit then takes the index as staged,
# so no file is stored with CRLF. Anything staged earlier is committed too, so check `git status` first.
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$out = Join-Path $here "git_commit_out.txt"
Set-Location $here
$msg = $args[0]
$paths = @($args | Select-Object -Skip 1)
"" | Out-File $out
git add -- @paths *>> $out
git -c core.autocrlf=false -c user.name="Shashank Kumar" -c user.email=shashankchoudhary792@gmail.com commit -m $msg *>> $out
git log --oneline -n 3 *>> $out
