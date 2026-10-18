$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -DNF_SOURCE_ROAD_ENDPOINT_RENDER -DNF_NATIVE_ENDPOINT_RENDER -DNF_ROAD_ATTRIBUTE_CORRECTION -DNF_VISIBILITY_QUEUE_CAPACITY=32 work/camera/threaded_preview.c work/camera/menu_renderer_gpu.c work/camera/road_source_ring.c work/camera/road_camera_continuous.c work/camera/road_near_continuous.c work/camera/road_point_project_continuous.c work/camera/road_near_attributes.c work/camera/road_polygon_clip.c work/camera/obj_tile.c work/camera/render_handoff.c work/camera/render_submission.c work/camera/indexed_copy.c work/camera/hardware_submission.c work/camera/layer_snapshot.c work/camera/submission_handoff.c work/camera/presentation_submission.c work/camera/scene_packet.c work/camera/snapshot_store.c work/camera/presentation_timeline.c work/camera/rigid_motion.c work/camera/frame_clock.c -lopengl32 -lgdi32 -luser32 -lm -o work/camera/threaded-preview.exe
exit $LASTEXITCODE


