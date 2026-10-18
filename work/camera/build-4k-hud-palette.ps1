$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared work/camera/owned_gpu_segmented_4k_hud_reuse_candidate.c work/camera/owned_window_input.c work/camera/owned_controller_service.c work/camera/obj_tile_palette_candidate.c work/camera/native_model.c work/camera/native_wall_source.c work/camera/wall_edge_order.c work/camera/wall_source_uv.c work/camera/road_camera_continuous.c work/camera/road_point_project_continuous.c -lopengl32 -lgdi32 -o work/camera/owned-gpu-segmented-4k-hud-palette-candidate.dll
if($LASTEXITCODE){throw 'Native owned GPU build failed'}




& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared "-Wl,--export-all-symbols" work/camera/obj_tile.c -o work/camera/obj-tile-reference-component.dll
if($LASTEXITCODE){throw "Reference component failed"}
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared "-Wl,--export-all-symbols" work/camera/obj_tile_palette_candidate.c -o work/camera/obj-tile-palette-component.dll
if($LASTEXITCODE){throw "Candidate component failed"}

