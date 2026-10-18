$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -ffp-contract=off -shared work/camera/wall_visibility_batch.c -o work/camera/wall-visibility-batch.dll
if($LASTEXITCODE){throw 'Wall visibility batch build failed'}
