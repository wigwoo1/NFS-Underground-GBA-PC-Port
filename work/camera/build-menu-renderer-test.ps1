$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 work/camera/menu_renderer_gpu_test.c work/camera/menu_renderer_gpu.c work/camera/obj_tile.c work/camera/hardware_submission.c work/camera/layer_snapshot.c -lopengl32 -lgdi32 -luser32 -lm -o work/camera/menu-renderer-gpu-test.exe
exit $LASTEXITCODE
