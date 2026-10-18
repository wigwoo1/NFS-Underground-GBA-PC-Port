import runpy
import owned_sampled_world_frame as assembly
from owned_native_frame_join import join_frame
assembly.join_frame=join_frame
runpy.run_path('work/camera/run_native_batch_compact_all_diagnostics.py',run_name='__main__')
