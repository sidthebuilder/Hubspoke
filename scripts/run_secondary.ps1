# Forks, replay and canary in parallel (resumable: finished outputs are skipped, missing main runs are logged
# and picked up by the next call). Usage: run_secondary.ps1 [forks_workers] [replay_workers] [canary_workers]
$here = Split-Path -Parent $PSScriptRoot  # the repository folder (this script is one level down)
$cli = Join-Path $here "scripts\run_cli.ps1"
$w = @(24, 24, 12)
for ($i = 0; $i -lt [Math]::Min($args.Count, 3); $i++) { $w[$i] = [int]$args[$i] }
Start-Process powershell -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cli, "forks", "--workers", "$($w[0])") -WindowStyle Hidden
Start-Process powershell -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cli, "replay", "--workers", "$($w[1])") -WindowStyle Hidden
Start-Process powershell -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cli, "canary", "--workers", "$($w[2])") -WindowStyle Hidden
