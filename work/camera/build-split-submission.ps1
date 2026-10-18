$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared work/camera/render_submission.c work/camera/indexed_copy.c work/camera/render_handoff.c work/camera/hardware_submission.c work/camera/layer_snapshot.c work/camera/presentation_submission.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c work/camera/rigid_motion.c -lm -o work/camera/split-submission.dll
exit $LASTEXITCODE

