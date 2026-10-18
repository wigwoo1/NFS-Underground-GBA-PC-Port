$ErrorActionPreference = 'Stop'
$compiler = 'C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin/gcc.exe'
$inputs = @(
 'work/camera/owned_original_endpoint_candidate.c',
 'work/camera/owned_hud_snapshot_bound_short_lock_candidate.c',
 'work/camera/native_wall_source.c',
 'work/camera/native_model.c',
 'work/camera/obj_tile_plane_candidate.c',
 'work/camera/road_point_project_continuous.c',
 'work/camera/road_camera_continuous.c',
 'work/camera/wall_edge_order.c',
 'work/camera/wall_source_uv.c',
 'work/camera/owned_window_input.c',
 'work/camera/owned_controller_service.c'
)
& $compiler '-BC:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin/' -O2 -shared @inputs -o work/camera/owned-original-endpoint-candidate.dll -lopengl32 -lgdi32 -luser32 -lxinput
if ($LASTEXITCODE -ne 0) { throw 'HUD short-lock bundle build failed' }

