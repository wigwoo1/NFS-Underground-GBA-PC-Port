param(
 [string]$RomPath='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',
 [ValidateRange(0,30)][int]$SmokeSeconds=0,
 [switch]$BufferedPresentation,
 [switch]$StartAtTitle
)
$ErrorActionPreference='Stop'
$nfCamera=$PSScriptRoot
$nfState=if($StartAtTitle){Join-Path (Split-Path -Parent $nfCamera) 'fix-menu/menu-4.state'}else{Join-Path (Split-Path -Parent $nfCamera) 'driving.state'}
foreach($nfName in @('threaded-preview.exe','visibility-probe-wide.dll','road-correction-reciprocal.bin','verify_threaded_session.py')){if(!(Test-Path -LiteralPath (Join-Path $nfCamera $nfName))){throw "Missing prototype dependency: $nfName"}}
if(!(Test-Path -LiteralPath $RomPath) -or !(Test-Path -LiteralPath $nfState)){throw 'ROM or selected checkpoint unavailable.'}
$nfLogs=Join-Path $nfCamera 'prototype-runs';New-Item -ItemType Directory -Path $nfLogs -Force | Out-Null
$nfPrefix=Join-Path $nfLogs ('threaded-launch-'+[guid]::NewGuid().ToString('N'))
$nfManifest=@{status='RUNNING';live_road_attributes=$true;live_model_bounds=$true;rom=$RomPath;state=$nfState;rom_sha256=(Get-FileHash -LiteralPath $RomPath -Algorithm SHA256).Hash;state_sha256=(Get-FileHash -LiteralPath $nfState -Algorithm SHA256).Hash;prefix=$nfPrefix;smoke_seconds=$SmokeSeconds;presentation_lag_ns=$(if($BufferedPresentation){33333334}else{16666667})}
$nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
$nfSaved=@{}
foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){$nfSaved[$nfItem.Name]=$nfItem.Value;Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
try{
 $env:NF_THREADED_LAG_NS="$($nfManifest.presentation_lag_ns)"
 $env:NF_LIVE_ROAD_ATTRIBUTES='1';$env:NF_CONTINUOUS_ROAD_UV='1';$env:NF_ROAD_RECIPROCAL=Join-Path $nfCamera 'road-correction-reciprocal.bin'
 if($SmokeSeconds){$env:NF_THREADED_CONTROLLER='1';$nfSeconds=$SmokeSeconds}
 else{$env:NF_THREADED_INTERACTIVE='1';$nfSeconds=3600}
 Write-Host 'Experimental threaded native prototype. No audio yet.'
 if($StartAtTitle){Write-Host 'Title/menu prototype: Enter opens name entry. Later menus and race transitions remain under development.'}
 if($BufferedPresentation){Write-Host 'Buffered presentation enabled: adds 16.7 ms of display latency.'}
 Write-Host 'Keyboard: Z accelerate, X brake, arrows steer, Enter start, Backspace select, A/S shoulder actions.'
 Write-Host 'Xbox: A/right trigger accelerate, B/left trigger brake, left stick steer. Space pauses; Escape closes.'
 & (Join-Path $nfCamera 'threaded-preview.exe') (Join-Path $nfCamera 'visibility-probe-wide.dll') $RomPath $nfState $nfPrefix "$nfSeconds" | Tee-Object -FilePath "$nfPrefix-host.log"
 $nfExit=$LASTEXITCODE;$nfManifest.exit_code=$nfExit;$nfManifest.status=if($nfExit){'HOST_FAILED'}else{'HOST_COMPLETE'}
 $nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
 if($nfExit){throw "Prototype failed with code $nfExit. See $nfPrefix-host.log"}
 $nfPython=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
 if(Test-Path -LiteralPath $nfPython){& $nfPython (Join-Path $nfCamera 'verify_threaded_session.py') "$nfPrefix-session.json";if($LASTEXITCODE){throw 'Recorded session verification failed.'}}
 Write-Host "Session: $nfPrefix-session.json"
}finally{
 foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
 foreach($nfName in $nfSaved.Keys){Set-Item -LiteralPath "Env:$nfName" -Value $nfSaved[$nfName]}
}
