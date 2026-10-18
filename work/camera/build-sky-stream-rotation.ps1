$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -DNF_SKY_STREAM_BUFFERS=3 -shared work/camera/owned_gpu_sky_rotation_candidate.c work/camera/owned_window_input.c work/camera/owned_controller_service.c work/camera/obj_tile.c work/camera/native_model.c work/camera/native_wall_source.c work/camera/wall_edge_order.c work/camera/wall_source_uv.c work/camera/road_camera_continuous.c work/camera/road_point_project_continuous.c -lopengl32 -lgdi32 -o work/camera/owned-sky-gpu-rotation.dll
if($LASTEXITCODE){throw 'Native owned GPU build failed'}
