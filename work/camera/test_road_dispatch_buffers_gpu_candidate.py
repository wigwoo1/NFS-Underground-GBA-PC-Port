import owned_sampled_road_sequence as roads
from owned_road_dispatch_buffers_candidate import clipped_camera_road
roads.clipped_camera_road=clipped_camera_road
import runpy
runpy.run_path('work/camera/test_segmented_original_gpu_parity.py',run_name='__main__')
