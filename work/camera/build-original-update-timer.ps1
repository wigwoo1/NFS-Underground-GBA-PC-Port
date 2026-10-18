$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared work/camera/owned_original_update_timer.c -o work/camera/owned-original-update-timer.dll
if($LASTEXITCODE){throw 'Original update diagnostic timer build failed'}
