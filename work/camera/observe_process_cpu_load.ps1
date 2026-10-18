# Read-only process CPU deltas. No command lines, paths, process control or priorities.
$taskRows = [System.Collections.Generic.List[object]]::new()
$taskPrevious = @{}
$taskPreviousNs = $null
$taskLogical = [Environment]::ProcessorCount
$taskFrequency = [System.Diagnostics.Stopwatch]::Frequency
for ($taskIndex=0; $taskIndex -lt 66; $taskIndex++) {
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
 Start-Sleep -Milliseconds 1000
}
$taskPath = Join-Path 'work/camera/prototype-runs' ('process-cpu-load-'+[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()+'.json')
@{logical_processors=$taskLogical; samples=@($taskRows); scope='Read-only one-second process CPU deltas; inaccessible/exited/new processes omitted; executable names and PID only; no GPU attribution or proof of stall causality'} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $taskPath -Encoding UTF8
Write-Output $taskPath
