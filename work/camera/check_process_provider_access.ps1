$ErrorActionPreference='Stop'
$stamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$ownedSession='NFSUG-ProcessProbe-'+$stamp
$dir=Join-Path (Get-Location) ('work/camera/prototype-runs/graphics-process-probe-'+$stamp)
New-Item -ItemType Directory -Path $dir | Out-Null
$etl=Join-Path $dir 'graphics.etl'
$providerFile=Join-Path $dir 'providers.txt'
@('Microsoft-Windows-Kernel-Process 0x10 5') | Set-Content -LiteralPath $providerFile -Encoding ascii
$startLog=& logman create trace $ownedSession -o $etl -f bincirc -max 16 -ct perf -pf $providerFile -ets 2>&1
$startCode=$LASTEXITCODE
$startLog | Set-Content (Join-Path $dir 'start.log')
$stopCode=$null
if($startCode -eq 0){
 try { Start-Sleep -Seconds 3; & logman query $ownedSession -ets 2>&1 | Set-Content (Join-Path $dir 'active.log') }
 finally { & logman stop $ownedSession -ets 2>&1 | Set-Content (Join-Path $dir 'stop.log');$stopCode=$LASTEXITCODE }
}
if($startCode -ne 0){
 & logman query $ownedSession -ets 2>&1 | Set-Content (Join-Path $dir 'failed-session-query.log')
 if($LASTEXITCODE -eq 0){ & logman stop $ownedSession -ets 2>&1 | Set-Content (Join-Path $dir 'failure-cleanup.log');$stopCode=$LASTEXITCODE }
}
@{session=$ownedSession;start_exit=$startCode;stop_exit=$stopCode;etl_exists=(Test-Path -LiteralPath $etl);scope='Three-second separately owned graphics-provider capability trace. Expanded source-guided provider set; no game cadence or display identity proof; no other session changed.'} | ConvertTo-Json | Set-Content (Join-Path $dir 'result.json')
Get-Content (Join-Path $dir 'result.json')
if($startCode -eq 0 -and $stopCode -eq 0 -and (Test-Path -LiteralPath $etl)){
 & tracerpt $etl -summary (Join-Path $dir 'summary.txt') -report (Join-Path $dir 'report.xml') -y 2>&1 | Set-Content (Join-Path $dir 'decode.log')
 Write-Output ('Decode exit: '+$LASTEXITCODE)
}
Write-Output $dir

