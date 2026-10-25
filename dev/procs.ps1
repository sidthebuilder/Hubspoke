# Dev helper: which python / powershell processes of this project are alive (command lines), into procs_out.txt.
$out = Join-Path (Split-Path -Parent $PSScriptRoot) "procs_out.txt"
"$(Get-Date -Format s)" | Out-File -Encoding utf8 $out
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'powershell.exe'" |
    Where-Object { $_.CommandLine -like "*hubspoke*" } |
    Select-Object ProcessId, ParentProcessId, @{n="cmd"; e={ $_.CommandLine.Substring(0, [math]::Min(200, $_.CommandLine.Length)) }} |
    Format-Table -AutoSize | Out-File -Append -Width 300 -Encoding utf8 $out
