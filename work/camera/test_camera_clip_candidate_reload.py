import runpy
import owned_sampled_road_sequence as sequence
from owned_camera_clip_transaction import clipped_camera_road
sequence.clipped_camera_road=clipped_camera_road
runpy.run_path('work/camera/test_continuous_sky_worker_reload.py',run_name='__main__')
