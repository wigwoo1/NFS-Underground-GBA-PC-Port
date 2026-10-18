param([ValidateRange(1,120)][int]$Seconds=61,[uint32]$CaptureRefresh=12350,[switch]$TimingOnly,[ValidateRange(0,60)][int]$DenseFrames=0,[ValidateRange(0,100000000)][uint64]$PresentationLagNs=16666667,[switch]$WindowLifecycle)
$ErrorActionPreference='Stop'
$nfCamera=$PSScriptRoot
$nfRom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
$nfState=Join-Path (Split-Path -Parent $nfCamera) 'driving.state'
$nfPrefix=Join-Path $nfCamera ('prototype-runs/threaded-route-'+[guid]::NewGuid().ToString('N'))
$nfManifest=@{status='RUNNING';live_road_attributes=$true;live_model_bounds=$true;rom=$nfRom;state=$nfState;rom_sha256=(Get-FileHash -LiteralPath $nfRom).Hash;state_sha256=(Get-FileHash -LiteralPath $nfState).Hash;prefix=$nfPrefix;smoke_seconds=$Seconds;steering_route=$true;capture_refresh=$CaptureRefresh;timing_only=[bool]$TimingOnly;presentation_lag_ns=$PresentationLagNs;window_lifecycle=[bool]$WindowLifecycle}
$nfManifest.dense_frames=$DenseFrames
$nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
$nfSaved=@{}
foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){$nfSaved[$nfItem.Name]=$nfItem.Value;Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
try{
 $env:NF_LIVE_ROAD_ATTRIBUTES='1';$env:NF_CONTINUOUS_ROAD_UV='1';$env:NF_ROAD_RECIPROCAL=Join-Path $nfCamera 'road-correction-reciprocal.bin'
 $env:NF_THREADED_STEERING_ROUTE='1';$env:NF_THREADED_LAG_NS="$PresentationLagNs"
 if($WindowLifecycle){$env:NF_TEST_THREADED_WINDOW='1';$env:NF_TEST_THREADED_ACTUAL_WINDOW='1'}
 if($TimingOnly){$env:NF_THREADED_NO_READBACK='1'}else{$env:NF_THREADED_EXPORT_FRAME='1';$env:NF_THREADED_CAPTURE_REFRESH="$CaptureRefresh"}
 if($DenseFrames){$env:NF_THREADED_NO_READBACK='1';$env:NF_THREADED_DENSE_COUNT="$DenseFrames";$env:NF_THREADED_CAPTURE_REFRESH="$CaptureRefresh"}
 & (Join-Path $nfCamera 'threaded-preview.exe') (Join-Path $nfCamera 'visibility-probe-wide.dll') $nfRom $nfState $nfPrefix "$Seconds" | Tee-Object -FilePath "$nfPrefix-host.log"
 $nfManifest.exit_code=$LASTEXITCODE;$nfManifest.status=if($LASTEXITCODE){'HOST_FAILED'}else{'HOST_COMPLETE'}
 $nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
 if($nfManifest.exit_code){throw 'Steering capture host failed.'}
 & 'C:/Users/wigwo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $nfCamera 'verify_threaded_session.py') "$nfPrefix-session.json"
 if($LASTEXITCODE){throw 'Steering capture session verification failed.'}
 Write-Host "Session: $nfPrefix-session.json"
}finally{
 foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
 foreach($nfName in $nfSaved.Keys){Set-Item -LiteralPath "Env:$nfName" -Value $nfSaved[$nfName]}
}
