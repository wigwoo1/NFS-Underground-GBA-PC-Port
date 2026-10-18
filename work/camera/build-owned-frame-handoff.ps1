$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared work/camera/owned_frame_handoff.c -o work/camera/owned-frame-handoff.dll
if($LASTEXITCODE){throw 'Owned frame handoff build failed'}
