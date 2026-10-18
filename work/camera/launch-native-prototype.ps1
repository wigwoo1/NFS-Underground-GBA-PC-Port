param(
    [string]$RomPath='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',
    [ValidateRange(0,30)][int]$SmokeSeconds=0,
    [switch]$OptimizeSnapshots
)
$ErrorActionPreference='Stop'
$nfCamera=$PSScriptRoot
$nfWork=Split-Path -Parent $nfCamera
$nfRequired=@('native-endpoint-road-attributes.exe','visibility-probe-wide.dll','road-correction-reciprocal.bin')
foreach($nfName in $nfRequired){if(!(Test-Path -LiteralPath (Join-Path $nfCamera $nfName))){throw "Missing prototype dependency: $nfName"}}
if(!(Test-Path -LiteralPath $RomPath)){throw 'The supplied ROM is unavailable. Pass -RomPath with its current location.'}
$nfState=Join-Path $nfWork 'driving.state'
if(!(Test-Path -LiteralPath $nfState)){throw 'The driving checkpoint is unavailable.'}
$nfLogs=Join-Path $nfCamera 'prototype-runs'
New-Item -ItemType Directory -Path $nfLogs -Force | Out-Null
$nfRun=Join-Path $nfLogs ([guid]::NewGuid().ToString('N'))
# Isolate the runnable prototype from diagnostic capture/profiling settings.
$nfSaved=@{}
foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){$nfSaved[$nfItem.Name]=$nfItem.Value;Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
try{
    $env:NF_LIVE_HUD='1';$env:NF_LIVE_WORLD_CLASSIFIED='1';$env:NF_LIVE_ROAD_ATTRIBUTES='1'
    $env:NF_CONTINUOUS_CAMERA='1';$env:NF_CONTINUOUS_ROAD_UV='1'
    if($OptimizeSnapshots){$env:NF_LAYER_DIRTY='1'}
    $env:NF_ROAD_RECIPROCAL=Join-Path $nfCamera 'road-correction-reciprocal.bin'
    $env:NF_REFRESH_TRACE="$nfRun-input.csv"
    $env:NF_ENDPOINT_RAM_PREFIX="$nfRun-final"
    $nfManifest=@{status='RUNNING';rom=$RomPath;state=$nfState;rom_sha256=(Get-FileHash -LiteralPath $RomPath -Algorithm SHA256).Hash;state_sha256=(Get-FileHash -LiteralPath $nfState -Algorithm SHA256).Hash;input_trace="$nfRun-input.csv";log="$nfRun.log";ram_prefix="$nfRun-final";display_trace="$nfRun.csv";smoke_seconds=$SmokeSeconds}
    $nfManifest.optimized_snapshots=[bool]$OptimizeSnapshots
    $nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfRun-session.json"
    $nfArguments=@((Join-Path $nfCamera 'visibility-probe-wide.dll'),$RomPath,$nfState,"$nfRun.csv",'--paired-packets','--layer-sync','--delay-refreshes','8','--seconds')
    if($SmokeSeconds){$nfArguments+=@("$SmokeSeconds",'--controller','--window-buffer')}
    else{$nfArguments+=@('3600','--interactive')}
    Write-Host 'Experimental native 4K prototype, no audio. Original game logic; timing and physical Xbox verification remain incomplete.'
    Write-Host 'Keyboard: Z accelerate, X brake, arrows steer, Enter start, Backspace select, A/S shoulder actions. Xbox: A/B or triggers accelerate/brake, left stick steer.'
    Write-Host 'Right trigger accelerates; left trigger brakes. Space pauses; Escape closes. The driving checkpoint is loaded without saving changes.'
    & (Join-Path $nfCamera 'native-endpoint-road-attributes.exe') @nfArguments | Tee-Object -FilePath "$nfRun.log"
    $nfExit=$LASTEXITCODE
    $nfManifest.status=if($nfExit){'HOST_FAILED'}else{'HOST_COMPLETE'}
    $nfManifest.exit_code=$nfExit
    $nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfRun-session.json"
    if($nfExit){throw "Prototype exited with code $nfExit. See $nfRun.log"}
    Write-Host "Recorded session: $nfRun-session.json."
    $nfPython=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if(Test-Path -LiteralPath $nfPython){
        & $nfPython (Join-Path $nfCamera 'verify_prototype_session.py') "$nfRun-session.json" | Tee-Object -FilePath "$nfRun-verification.log"
        if($LASTEXITCODE){throw "Recorded session verification failed. See $nfRun-session-verification.json"}
        Write-Host 'Recorded inputs, native presentation trace and final original game state verified. Smooth frame pacing and physical Xbox response remain unverified.'
    }else{
        Write-Host 'Replay verifier runtime unavailable. The session is recorded; run verify_prototype_session.py with this manifest when Python is available.'
    }
}finally{
    foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
    foreach($nfName in $nfSaved.Keys){Set-Item -LiteralPath "Env:$nfName" -Value $nfSaved[$nfName]}
}
