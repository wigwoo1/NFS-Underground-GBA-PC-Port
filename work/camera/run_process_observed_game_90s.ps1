param([string]$Renderer='work/camera/run_queued_single_candidate.py')
$pythonPath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$runStamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$gameOut=Join-Path 'work/camera/prototype-runs' ('observed-game-'+$runStamp+'.stdout.txt')
$gameErr=Join-Path 'work/camera/prototype-runs' ('observed-game-'+$runStamp+'.stderr.txt')
$gameProcess=$null
$gameArgs=@($Renderer,'--capture-probe-candidate','viewport-sky-capture-probe.dll','--interpolate','--startup-readiness','--full-scene','--background-prepare','--precompute-world-samples','--presentation-delay-refreshes','12','--python-thread-switch-ms','1','--capture-sky','--interpolate-sky','--continuous-sky','--native-present-callback','--original-update-boundary','--swap-interval','0','--producer-cycles','--smoke-seconds','90','--smoke-steering','--smoke-repeat-pause')
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
  $gameProcess=Start-Process -FilePath $pythonPath -ArgumentList $gameArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $gameOut -RedirectStandardError $gameErr
 } elseif ($gameProcess.HasExited) { break }
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

