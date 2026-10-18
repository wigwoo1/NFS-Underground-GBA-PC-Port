$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared -DNF_ROAD_ATTRIBUTE_CORRECTION work/camera/road_transition_gpu_probe.c work/camera/road_near_attributes.c work/camera/obj_tile.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c work/camera/rigid_motion.c work/camera/frame_clock.c -lopengl32 -lgdi32 -luser32 -lm -o work/camera/road-transition-gpu-probe.dll
exit $LASTEXITCODE
