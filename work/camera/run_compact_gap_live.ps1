param([string]$Selection,[string]$Label)
$env:NFSUG_SCENE_MEMORY_TWO_ENTRY=$Selection
$env:NFSUG_CORRECTED_ROAD_PAIR='0'
$env:NFSUG_NATIVE_PORTAL_PARENT_BATCH='0'
$env:NFSUG_CHILD_GC_TRACE='1'
$env:NFSUG_CHILD_STARTUP_GC='1'
$env:NFSUG_SINGLE_JOIN_SCENE_PACK='1'
$env:NFSUG_DIRECT_SHARED_INPUT_DECODE='1'
$env:NFSUG_HUD_CALLBACK_STAGE_BATCH='1'
$env:NFSUG_ROAD_FLAT_JOIN='1'
$env:NFSUG_ROAD_RECORD_CONSTRUCTION='1'
$env:NFSUG_FRAME_PREFIX_CACHE='1'
$env:NFSUG_STREAMING_OUTPUT='1'
$taskLog=Join-Path 'work/camera' ('two-entry-'+$Label+'.log')
& 'C:/Users/wigwo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'work/camera/run_compact_gap_live.py' --capture-probe-candidate viewport-sky-private-capture-probe.dll --process-prepare --shared-process-output --interpolate --startup-readiness --full-scene --background-prepare --precompute-world-samples --presentation-delay-refreshes 12 --python-thread-switch-ms 1 --capture-sky --interpolate-sky --continuous-sky --native-present-callback --original-update-boundary --native-capture-batch --producer-cycles --smoke-seconds 30 --smoke-steering --smoke-repeat-pause *> $taskLog
exit $LASTEXITCODE



