"""Explicit experimental native frame joining on native road clip runner."""
import runpy,json
import owned_sampled_world_frame as module
from owned_native_frame_join import join_frame,trace
calls=0
def counted(*args):
 global calls
 calls+=1
 return join_frame(*args)
module.join_frame=counted
module.join_frame_trace=trace
ns=runpy.run_path('work/camera/run_camera_clip_candidate.py',run_name='__main__')['namespace']
assert calls>0
ns['report']['native_frame_join_calls']=calls;ns['out'].write_text(json.dumps(ns['report'],indent=2));print('PASS native frame join calls',calls)
