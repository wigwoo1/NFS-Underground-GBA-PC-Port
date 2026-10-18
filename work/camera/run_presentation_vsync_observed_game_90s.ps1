param([string]$Renderer='work/camera/run_queued_single_candidate.py')
$pythonPath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$runStamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$gameOut=Join-Path 'work/camera/prototype-runs' ('observed-game-'+$runStamp+'.stdout.txt')
$gameErr=Join-Path 'work/camera/prototype-runs' ('observed-game-'+$runStamp+'.stderr.txt')
$gameProcess=$null
$gameArgs=@($Renderer,'--capture-probe-candidate','viewport-sky-capture-probe.dll','--interpolate','--startup-readiness','--full-scene','--background-prepare','--precompute-world-samples','--presentation-delay-refreshes','12','--python-thread-switch-ms','1','--capture-sky','--interpolate-sky','--continuous-sky','--native-present-callback','--original-update-boundary','--swap-interval','1','--producer-cycles','--show-smoke-window','--smoke-seconds','90','--smoke-steering','--smoke-repeat-pause')
# Read-only process CPU deltas. No command lines, paths, process control or priorities.
$taskRows = [System.Collections.Generic.List[object]]::new()
$taskPrevious = @{}
$taskPreviousNs = $null
$taskLogical = [Environment]::ProcessorCount
$taskFrequency = [System.Diagnostics.Stopwatch]::Frequency
for ($taskIndex=0; $taskIndex -lt 180; $taskIndex++) {
 $taskCurrent = @{}
 $taskSkipped = 0
 foreach ($taskProcess in Get-Process) {
  try {
   $taskKey = "$($taskProcess.Id):$($taskProcess.StartTime.ToUniversalTime().Ticks)"
   $taskCurrent[$taskKey] = @{ pid=$taskProcess.Id; name=$taskProcess.ProcessName; cpu=$taskProcess.TotalProcessorTime.TotalSeconds }
  } catch { $taskSkipped++ }
  finally { $taskProcess.Dispose() }
 }
 $taskNs = [long]([System.Diagnostics.Stopwatch]::GetTimestamp()*1000000000.0/$taskFrequency)
 if ($null -ne $taskPreviousNs) {
  $taskSeconds = ($taskNs-$taskPreviousNs)/1000000000.0
  $taskDelta = foreach ($taskKey in $taskCurrent.Keys) {
   if ($taskPrevious.ContainsKey($taskKey)) {
    $taskValue = $taskCurrent[$taskKey]
    $taskCpuDelta = $taskValue.cpu-$taskPrevious[$taskKey].cpu
    if ($taskCpuDelta -ge 0) { [pscustomobject]@{ pid=$taskValue.pid; name=$taskValue.name; cpu_seconds=$taskCpuDelta; logical_cpu_equivalents=$taskCpuDelta/$taskSeconds; system_capacity_fraction=$taskCpuDelta/$taskSeconds/$taskLogical } }
   }
  }
  $taskRows.Add([pscustomobject]@{begin_ns=$taskPreviousNs; end_ns=$taskNs; accessible_processes=$taskCurrent.Count; skipped_processes=$taskSkipped; top=@($taskDelta | Sort-Object cpu_seconds -Descending | Select-Object -First 12)})
 }
 $taskPrevious=$taskCurrent
 $taskPreviousNs=$taskNs
 if ($null -eq $gameProcess) {
  $gameProcess=Start-Process -FilePath $pythonPath -ArgumentList $gameArgs -WindowStyle Normal -PassThru -RedirectStandardOutput $gameOut -RedirectStandardError $gameErr
  $traceArgs=@('--process_id',[string]$gameProcess.Id,'--session_name',('NFSUG-'+$runStamp),'--timed','110','--terminate_after_timed','--terminate_on_proc_exit','--no_console_stats','--no_track_input','--qpc_time','--output_file',('work/camera/prototype-runs/presentation-'+$runStamp+'.csv'))
  @{game_pid=$gameProcess.Id;session=('NFSUG-'+$runStamp);trace_args=$traceArgs;game_args=$gameArgs;working_directory=(Get-Location).Path} | ConvertTo-Json -Depth 4 | Set-Content ('work/camera/prototype-runs/presentation-'+$runStamp+'.config.json') -Encoding UTF8
  $traceProcess=Start-Process -FilePath 'C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe' -ArgumentList $traceArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput ('work/camera/prototype-runs/presentation-'+$runStamp+'.stdout.txt') -RedirectStandardError ('work/camera/prototype-runs/presentation-'+$runStamp+'.stderr.txt')
 } elseif ($gameProcess.HasExited) { break }
 if ($taskIndex -eq 10 -and -not $gameProcess.HasExited) {
  $windowArgs=@('work/camera/check_owned_game_window.py',[string]$gameProcess.Id,('work/camera/prototype-runs/presentation-'+$runStamp+'.window.json'))
  $windowProbe=Start-Process -FilePath $pythonPath -ArgumentList $windowArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput ('work/camera/prototype-runs/presentation-'+$runStamp+'.window.stdout.txt') -RedirectStandardError ('work/camera/prototype-runs/presentation-'+$runStamp+'.window.stderr.txt')
 }
 Start-Sleep -Milliseconds 1000
}
$taskPath = Join-Path 'work/camera/prototype-runs' ('process-cpu-load-'+[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()+'.json')
@{logical_processors=$taskLogical; samples=@($taskRows); scope='Read-only one-second process CPU deltas; inaccessible/exited/new processes omitted; executable names and PID only; no GPU attribution or proof of stall causality'} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $taskPath -Encoding UTF8
Write-Output $taskPath

if (-not $gameProcess.HasExited) { throw 'Game process still active after observation bound; do not restart it.' }
$gameProcess.WaitForExit()
Get-Content -LiteralPath $gameOut
Get-Content -LiteralPath $gameErr
if ($gameProcess.ExitCode -ne 0) { throw ('Game failed: '+$gameProcess.ExitCode) }

$traceProcess.WaitForExit()
Write-Output ('Presentation trace exit: '+$traceProcess.ExitCode)
$traceCsv = 'work/camera/prototype-runs/presentation-'+$runStamp+'.csv'
if ($traceProcess.ExitCode -ne 0) { throw ('Presentation trace failed: '+$traceProcess.ExitCode) }
if (-not (Test-Path -LiteralPath $traceCsv -PathType Leaf)) { throw ('Presentation trace produced no CSV: '+$traceCsv+'; completed game evidence remains valid, display observation is unavailable.') }
$traceRows = @(Import-Csv -LiteralPath $traceCsv)
if ($traceRows.Count -eq 0) { throw ('Presentation trace CSV has no observations: '+$traceCsv) }
foreach ($traceRow in $traceRows) {
 if ($null -eq $traceRow.ProcessID -or [long]$traceRow.ProcessID -ne $gameProcess.Id) { throw 'Presentation trace contains a missing or unexpected game PID.' }
}
Write-Output $traceCsv







