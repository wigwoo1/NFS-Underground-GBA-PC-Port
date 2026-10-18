param([switch]$Wide,[switch]$ReferencePalette)
$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
[string[]]$nfCapacityArgs=if($Wide){@('-DNF_VISIBILITY_QUEUE_CAPACITY=32','-DNF_LAYER_QUEUE_CAPACITY=40')}else{@()}
$nfOutput=if($Wide){'work/camera/visibility-probe-wide.dll'}else{'work/camera/visibility-probe.dll'}
if($ReferencePalette){$nfCapacityArgs+=@('-DNF_REFERENCE_PALETTE_EXPANSION');$nfOutput=if($Wide){'work/camera/visibility-probe-wide-reference-palette.dll'}else{'work/camera/visibility-probe-reference-palette.dll'}}
& "$nfCompiler/gcc.exe" @nfCapacityArgs "-B$nfCompiler/" -O2 -shared -DNF_VISIBILITY_CAPTURE -DBUILD_STATIC -DM_CORE_GBA -DUSE_DEBUGGERS -D_GNU_SOURCE '-D_WIN32_WINNT=0x0600' '-Iwork/mgba-0.10.5/include' '-Iwork/mgba-build/include' work/probe-sky-reader-phase.c work/camera/layer_snapshot.c work/camera/native_scene_executor.c work/camera/native_geometry_sources_sky_candidate.c work/camera/native_initial_page.c work/camera/native_sprite.c work/camera/native_model.c work/camera/native_wall.c work/camera/native_wall_source.c work/camera/wall_edge_order.c work/camera/wall_source_uv.c work/camera/native_road_source_decode.c work/camera/road_source_ring.c work/camera/road_camera_continuous.c work/camera/road_point_project_continuous.c work/camera/road_near_continuous.c work/camera/road_clip_continuous.c work/camera/bitmap_glyph.c work/camera/bitmap_layer.c work/camera/object_projection.c work/camera/object_callback.c work/camera/object_ground.c work/camera/draw_palette.c work/camera/native_visibility.c work/camera/visibility_snapshot.c work/camera/visibility_pose.c work/camera/ordered_dispatch.c work/camera/region_executor.c work/camera/scene_command_plan.c work/camera/road_polygon_clip.c work/camera/native_surface.c work/camera/indexed_copy.c work/camera/rigid_motion.c work/camera/scene_assembly.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c outputs/nfsug-research/native_span.c work/mgba-build/libmgba.a -lws2_32 -lshlwapi -lole32 -luuid -o work/camera/viewport-sky-reader-phase.dll
exit $LASTEXITCODE





