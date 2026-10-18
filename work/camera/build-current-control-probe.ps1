$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -DNF_VISIBILITY_CAPTURE -shared -DBUILD_STATIC -DM_CORE_GBA -DUSE_DEBUGGERS -D_GNU_SOURCE '-D_WIN32_WINNT=0x0600' '-Iwork/mgba-0.10.5/include' '-Iwork/mgba-build/include' work/probe.c work/camera/draw_palette.c work/camera/native_visibility.c work/camera/visibility_snapshot.c work/camera/native_surface.c work/camera/rigid_motion.c work/camera/scene_assembly.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c outputs/nfsug-research/native_span.c work/mgba-build/libmgba.a -lws2_32 -lshlwapi -lole32 -luuid -o work/camera/current-control-probe.dll
exit $LASTEXITCODE


