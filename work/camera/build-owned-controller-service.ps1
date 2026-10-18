$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared work/camera/owned_controller_service.c -o work/camera/owned-controller-service.dll
if($LASTEXITCODE){throw 'Controller service build failed'}
