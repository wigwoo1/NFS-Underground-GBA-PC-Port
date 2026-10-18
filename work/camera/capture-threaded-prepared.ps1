param([ValidateRange(8,32)][double]$SourceDelayRefreshes=8,[switch]$OwnedRootEndpoint,[switch]$SampledDrawScene,[switch]$TransitionDrawScene,[switch]$DisplayPalette,[switch]$IndexedEntrants,[switch]$FocalSample,[switch]$NativeBitmapText,[switch]$SelectionRoute,[string]$Checkpoint="",[ValidateRange(1,120)][int]$Seconds=3,[uint32]$CaptureRefresh=0,[switch]$TimingOnly,[switch]$ThreadCPUProfile,[switch]$WarmNative,[switch]$ExactSceneCache,[switch]$PrefillSceneCache,[switch]$VerifySceneCache,[ValidateRange(0,60)][int]$DenseFrames=0,[ValidateRange(0,100000000)][uint64]$PresentationLagNs=16666667,[switch]$WindowLifecycle)
$ErrorActionPreference='Stop'
if($FocalSample -and (-not $DisplayPalette -or -not $TransitionDrawScene)){throw 'FocalSample requires DisplayPalette and TransitionDrawScene.'}
if($IndexedEntrants -and (-not $DisplayPalette -or -not $TransitionDrawScene)){throw 'IndexedEntrants requires DisplayPalette and TransitionDrawScene.'}
$nfCamera=$PSScriptRoot
$nfRom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
$nfState=if($Checkpoint){$Checkpoint}else{Join-Path $nfCamera 'prototype-runs/menu-navigation/quick-1-release.state'}
$nfPrefix=Join-Path $nfCamera ('prototype-runs/threaded-prepared-'+[guid]::NewGuid().ToString('N'))
$nfManifest=@{status='RUNNING';live_road_attributes=$true;live_model_bounds=$true;rom=$nfRom;state=$nfState;rom_sha256=(Get-FileHash -LiteralPath $nfRom).Hash;state_sha256=(Get-FileHash -LiteralPath $nfState).Hash;prefix=$nfPrefix;smoke_seconds=$Seconds;steering_route=$false;selection_route=[bool]$SelectionRoute;owned_root_endpoint_diagnostic=[bool]$OwnedRootEndpoint;source_delay_refreshes=$SourceDelayRefreshes;capture_refresh=$CaptureRefresh;timing_only=[bool]$TimingOnly;presentation_lag_ns=$PresentationLagNs;window_lifecycle=[bool]$WindowLifecycle}
$nfManifest.sampled_draw_scene=[bool]($SampledDrawScene -or $TransitionDrawScene)
$nfManifest.transition_draw_scene=[bool]$TransitionDrawScene
$nfManifest.display_palette=[bool]$DisplayPalette
$nfManifest.indexed_entrants=[bool]$IndexedEntrants
$nfManifest.focal_sample=[bool]$FocalSample
$nfManifest.prefill_scene_cache=[bool]$PrefillSceneCache
$nfManifest.exact_scene_cache=[bool]$ExactSceneCache
$nfManifest.verify_scene_cache=[bool]$VerifySceneCache
$nfManifest.native_warmup=[bool]$WarmNative
$nfManifest.thread_cpu_profile=[bool]$ThreadCPUProfile
$nfManifest.native_bitmap_text_transport=[bool]$NativeBitmapText
$nfManifest.dense_frames=$DenseFrames
$nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
$nfSaved=@{}
foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){$nfSaved[$nfItem.Name]=$nfItem.Value;Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
try{
 $env:NF_TEST_SOURCE_DELAY_REFRESHES="$SourceDelayRefreshes";$env:NF_LIVE_ROAD_ATTRIBUTES='1';$env:NF_CONTINUOUS_ROAD_UV='1';$env:NF_ROAD_RECIPROCAL=Join-Path $nfCamera 'road-correction-reciprocal.bin'
 if($PrefillSceneCache){$env:NF_TEST_EXACT_SCENE_CACHE='1';$env:NF_TEST_EXACT_SCENE_PREFILL='1'}
 if($ExactSceneCache){$env:NF_TEST_EXACT_SCENE_CACHE='1'}
 if($VerifySceneCache){$env:NF_TEST_EXACT_SCENE_CACHE='1';$env:NF_TEST_EXACT_SCENE_CACHE_VERIFY='1'}
 if($WarmNative){$env:NF_TEST_NATIVE_WARMUP='1'}
 if($ThreadCPUProfile){$env:NF_TEST_THREAD_CPU_PROFILE='1'}
 if($NativeBitmapText){$env:NF_TEST_NATIVE_BITMAP_TEXT='1'}
 if($FocalSample){$env:NF_TEST_FOCAL_SAMPLE='1'}
 if($IndexedEntrants){$env:NF_TEST_INDEXED_ENTRANTS='1'}
 if($DisplayPalette){$env:NF_TEST_DISPLAY_PALETTE='1';$env:NF_CAPTURE_WALL_OUTPUT_INDICES='1'}
 if($TransitionDrawScene){$env:NF_TEST_TRANSITION_DRAW_SCENE='1';$env:NF_CAPTURE_MODEL_VIEWS='1'}
 if($SampledDrawScene){$env:NF_TEST_SAMPLED_DRAW_SCENE='1';$env:NF_CAPTURE_MODEL_VIEWS='1'}
 if($OwnedRootEndpoint){$env:NF_TEST_OWNED_ROOT_ENDPOINT='1';$env:NF_CAPTURE_MODEL_VIEWS='1'}
 if($SelectionRoute){$env:NF_TEST_THREADED_CAR_SELECTION='1';$env:NF_CAPTURE_MODEL_VIEWS='1'};$env:NF_TEST_THREADED_NEUTRAL='1';$env:NF_THREADED_LAG_NS="$PresentationLagNs"
 if($WindowLifecycle){$env:NF_TEST_THREADED_WINDOW='1';$env:NF_TEST_THREADED_ACTUAL_WINDOW='1'}
 if($TimingOnly){$env:NF_THREADED_NO_READBACK='1'}else{$env:NF_THREADED_EXPORT_FRAME='1';$env:NF_THREADED_CAPTURE_REFRESH="$CaptureRefresh"}
 if($DenseFrames){$env:NF_THREADED_NO_READBACK='1';$env:NF_THREADED_DENSE_COUNT="$DenseFrames";$env:NF_THREADED_CAPTURE_REFRESH="$CaptureRefresh"}
 & (Join-Path $nfCamera 'threaded-preview.exe') (Join-Path $nfCamera 'visibility-probe-wide.dll') $nfRom $nfState $nfPrefix "$Seconds" | Tee-Object -FilePath "$nfPrefix-host.log"
 $nfManifest.exit_code=$LASTEXITCODE;$nfManifest.status=if($LASTEXITCODE){'HOST_FAILED'}else{'HOST_COMPLETE'}
 $nfManifest | ConvertTo-Json | Set-Content -LiteralPath "$nfPrefix-session.json"
 if($nfManifest.exit_code){throw 'Prepared frontend capture host failed.'}
 & 'C:/Users/wigwo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $nfCamera 'verify_threaded_session.py') "$nfPrefix-session.json"
 if($LASTEXITCODE){throw 'Prepared frontend capture session verification failed.'}
 Write-Host "Session: $nfPrefix-session.json"
}finally{
 foreach($nfItem in Get-ChildItem Env:){if($nfItem.Name.StartsWith('NF_')){Remove-Item -LiteralPath "Env:$($nfItem.Name)"}}
 foreach($nfName in $nfSaved.Keys){Set-Item -LiteralPath "Env:$nfName" -Value $nfSaved[$nfName]}
}

