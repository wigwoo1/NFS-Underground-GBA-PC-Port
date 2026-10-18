$ErrorActionPreference='Stop'
$stamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$base='work/camera/prototype-runs/graphics-owned-game-'+$stamp
$pythonPath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskGameArgs=@('work/camera/run_source_compact_single_candidate.py','--capture-probe-candidate','viewport-sky-capture-probe.dll','--interpolate','--startup-readiness','--full-scene','--background-prepare','--precompute-world-samples','--presentation-delay-refreshes','12','--python-thread-switch-ms','1','--capture-sky','--interpolate-sky','--continuous-sky','--native-present-callback','--original-update-boundary','--swap-interval','1','--producer-cycles','--show-smoke-window','--smoke-seconds','30','--smoke-steering','--smoke-repeat-pause')
$game=Start-Process -FilePath $pythonPath -ArgumentList $taskGameArgs -WindowStyle Normal -PassThru -RedirectStandardOutput ($base+'.stdout.txt') -RedirectStandardError ($base+'.stderr.txt')
@{game_pid=$game.Id;arguments=$taskGameArgs;scope='Owned actual playable renderer30s, graphics-only3s observation subset; no physical frame identity claim'} | ConvertTo-Json -Depth 4 | Set-Content ($base+'.json')
Start-Sleep -Seconds 10
$traceOutput=@(& work/camera/check_graphics_only_events.ps1)
$traceOutput | Set-Content ($base+'.trace.log')
$traceDir=[string]$traceOutput[-1]
if(Test-Path -LiteralPath (Join-Path $traceDir 'graphics.etl')){
 & 'C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe' --etl_file (Join-Path $traceDir 'graphics.etl') --process_id $game.Id --output_file (Join-Path $traceDir 'owned-game.csv') --no_console_stats --no_track_input --no_track_gpu --qpc_time 2>&1 | Set-Content ($base+'.offline.log')
}
if(-not $game.WaitForExit(60000)){throw ('Owned game still active PID'+$game.Id+'; reobserve same process, do not restart.')}
Get-Content ($base+'.stdout.txt')
Get-Content ($base+'.stderr.txt')
Write-Output ('Game exit: '+$game.ExitCode)
Write-Output $base
Write-Output $traceDir
if($game.ExitCode -ne 0){throw 'Owned game failed'}

