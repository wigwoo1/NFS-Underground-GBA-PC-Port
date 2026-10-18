$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/he/work/toolchain/w64devkit/bin'
$env:PATH=($nfCompiler.Replace('/','\')+';'+$env:PATH)
& 'C:/NFSUG-Workspace/2026-09-13/he/work/toolchain/cmake/cmake-4.4.3-windows-x86_64/bin/cmake.exe' --build work/mgba-build --target mgba -j 8 *> work/build.log
if($LASTEXITCODE){Get-Content work/build.log -Tail 20;exit 1}
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared -DBUILD_STATIC -DM_CORE_GBA -DUSE_DEBUGGERS -D_GNU_SOURCE '-D_WIN32_WINNT=0x0600' '-Iwork/mgba-0.10.5/include' '-Iwork/mgba-build/include' work/probe.c work/camera/native_surface.c work/camera/rigid_motion.c work/camera/scene_assembly.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c outputs/nfsug-research/native_span.c work/mgba-build/libmgba.a -lws2_32 -lshlwapi -lole32 -luuid -o work/nfsprobe.dll
exit $LASTEXITCODE
