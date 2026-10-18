import runpy
import owned_sampled_world_frame as frame
from owned_native_frame_join import join_frame
frame.join_frame=join_frame
runpy.run_path('work/camera/capture_fullscene_sample_oracle.py',run_name='__main__')
