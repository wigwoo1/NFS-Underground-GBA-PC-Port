import runpy
import owned_sampled_world_frame as assembly
from owned_native_frame_join import trace
assembly.join_frame_trace=trace
runpy.run_path('work/camera/run_native_batch_frame_join_candidate.py',run_name='__main__')
