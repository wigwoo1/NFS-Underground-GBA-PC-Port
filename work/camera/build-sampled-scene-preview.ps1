$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -DNF_ROAD_ATTRIBUTE_CORRECTION work/camera/endpoint_scene_preview.c work/camera/road_near_attributes.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c work/camera/rigid_motion.c -lopengl32 -lgdi32 -luser32 -lm -o work/camera/sampled-scene-preview.exe
exit $LASTEXITCODE
