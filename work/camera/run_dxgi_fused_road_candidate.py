import owned_sampled_road_sequence as roads
from owned_camera_road_dispatch import clipped_camera_road
roads.clipped_camera_road=clipped_camera_road
import runpy
runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
