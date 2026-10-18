import runpy
import owned_sampled_world_frame as module
from owned_native_frame_join import join_frame,trace
module.join_frame=join_frame
module.join_frame_trace=trace
runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
