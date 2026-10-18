$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -DNF_NATIVE_ENDPOINT_RENDER -DNF_VISIBILITY_QUEUE_CAPACITY=32 work/camera/paced_preview.c work/camera/obj_tile.c work/camera/submission_handoff.c work/camera/presentation_submission.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c work/camera/rigid_motion.c work/camera/frame_clock.c -lopengl32 -lgdi32 -luser32 -lm -o work/camera/native-endpoint-preview.exe
exit $LASTEXITCODE


