"""Explicit experimental native camera clip runner; default launcher unchanged."""
import runpy,json
import owned_sampled_road_sequence as sequence
from owned_camera_clip_transaction import clipped_camera_road
calls=0
def counted(*args,**kwargs):
 global calls
 calls+=1
 return clipped_camera_road(*args,**kwargs)
sequence.clipped_camera_road=counted
namespace=runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
assert calls>0,'Candidate clipping not used'
report=namespace['report'];report['native_camera_clip_transaction_calls']=calls
namespace['out'].write_text(json.dumps(report,indent=2))
print('PASS native camera clipping candidate calls',calls)
