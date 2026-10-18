"""Isolated progressive sampling lifetime and native-authorized retirement."""
import inspect,textwrap,threading
from concurrent.futures import CancelledError
import live_native_hud_prefetch_generation_candidate as base
original=base.NativeLiveWorker._draw_intervals
source=textwrap.dedent(inspect.getsource(original))
old="slot_begin_ns=time.perf_counter_ns();alpha=slot['alpha'];frame,camera,models,bounds,detail=pair.sample(alpha);sample_end_ns=time.perf_counter_ns()\n  offsets,mask,total,_=pair.source_masks[alpha]"
new="slot_begin_ns=time.perf_counter_ns();alpha=slot['alpha']\n  with pair.cv:\n   frame,camera,models,bounds,detail=pair.sample(alpha)\n   offsets,mask,total,_=pair.source_masks[alpha];source_cameras=pair.source_cameras\n  sample_end_ns=time.perf_counter_ns()"
assert source.count(old)==1;source=source.replace(old,new).replace('*pair.source_cameras,alpha','*source_cameras,alpha')
namespace=dict(original.__globals__);exec(compile(source,'progressive-owned-sample-lifetime','exec'),namespace);owned_draw=namespace['_draw_intervals']
def draw(self,gpu,previous,current,generation,refresh,epoch,submitted_ns,dequeued_ns,scene):
 try:return owned_draw(self,gpu,previous,current,generation,refresh,epoch,submitted_ns,dequeued_ns,scene)
 except CancelledError:
  probe=base.Callback(lambda ctx:1)
  valid=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,probe,None)
  if valid==0:return False
  if valid!=1:raise ValueError('Invalid native retirement authority result')
  raise
base.NativeLiveWorker._draw_intervals=draw
