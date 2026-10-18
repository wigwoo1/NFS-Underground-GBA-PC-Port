$ErrorActionPreference='Continue'
Set-Location -LiteralPath 'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port'
$env:NFSUG_PROGRESSIVE_CPU_TRACE='1'
$env:NFSUG_PROGRESSIVE_CYCLE_TRACE='1'
$env:NFSUG_PROGRESSIVE_FINE_TRACE='1'
$env:NFSUG_PROGRESSIVE_FINE_FIRST='10952'
$env:NFSUG_PROGRESSIVE_FINE_LAST='10968'
$PSNativeCommandUseErrorActionPreference=$false
$env:NFSUG_SCENE_MEMORY_TWO_ENTRY='0'
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
$env:NFSUG_COMPACT_GAP_TRACE='0'
$env:NFSUG_MODEL_VISIT_INDEX='0'
$env:NFSUG_MODEL_VISIT_SELECTION_TRACE='1'
$taskLog='work/camera/slow-child-stage-trace-60s.log'
& 'C:/Users/wigwo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'work/camera/run_nonblocking_hud_compact_wrapper.py' --capture-probe-candidate viewport-sky-private-capture-probe.dll --process-prepare --shared-process-output --interpolate --startup-readiness --full-scene --background-prepare --precompute-world-samples --presentation-delay-refreshes 12 --python-thread-switch-ms 1 --capture-sky --interpolate-sky --continuous-sky --native-present-callback --original-update-boundary --native-capture-batch --producer-cycles --smoke-seconds 60 --smoke-steering --smoke-repeat-pause 2>&1 | Tee-Object -FilePath $taskLog
$code=$LASTEXITCODE
Get-Content -LiteralPath $taskLog -Tail 20
exit $code



