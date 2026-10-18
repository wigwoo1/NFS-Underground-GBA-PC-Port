import runpy
import owned_sampled_world_frame as module
from owned_native_frame_join import join_frame
module.join_frame=join_frame
runpy.run_path('work/camera/test_camera_clip_candidate_reload.py',run_name='__main__')
