"""Experimental bounded immutable HUD prefetch; native renderer remains single-threaded."""
import inspect,textwrap,time
import owned_native_source_segmented_release_worker_candidate as worker
import owned_renderer_dispatch_trace_install_candidate as dispatch
import owned_native_source_hud_cache_lease_session_candidate as hud
from owned_hud_preparation_timed_service_candidate import HudPreparationService
from owned_hud_shared_library_binding_candidate import HudFrameSnapshot
Base=worker.NativeSourceSession
class PrefetchSession(Base):
 def __init__(self):
  super().__init__();self.hud_service=HudPreparationService(self.source);self.hud_prefetch=[];self.hud_prefetch_taken=0;self.hud_authority=None
 def prefetch_hud(self,bases,epoch,generation):
  if self.closed:raise RuntimeError('Closed HUD prefetch')
  if type(bases) is not tuple or len(bases)>2 or any(type(x) is not bytes for x in bases):raise ValueError('Bounded immutable endpoint pair required')
  authority=(epoch,generation)
  if epoch<1 or generation<1 or (self.hud_authority is not None and authority<self.hud_authority):raise hud.NativeFrameIdentityError('Retired HUD prefetch generation')
  if self.hud_authority is not None and authority!=self.hud_authority:
   if self.pending is not None:raise hud.NativeFrameIdentityError('HUD reset while native frame pending')
   for base,future in self.hud_prefetch:self.hud_service.take(future).close()
   self.hud_prefetch=[]
   for snapshot in self.hud_snapshots:snapshot.close()
   self.hud_snapshots=[]
  self.hud_authority=authority
  for base,future in self.hud_prefetch:
   if not any(base is x for x in bases):self.hud_service.take(future).close()
  self.hud_prefetch=[(base,future) for base,future in self.hud_prefetch if any(base is x for x in bases)]
  for base in bases:
   if not any(x._base is base for x in self.hud_snapshots) and not any(x is base for x,f in self.hud_prefetch):self.hud_prefetch.append((base,self.hud_service.submit(base)))
  return dict(prefetch_count=len(self.hud_prefetch))
 def _take_hud(self,base):
  for index,(retained,future) in enumerate(self.hud_prefetch):
   if retained is base:
    begin=time.perf_counter_ns();ready=future.done();snapshot=self.hud_service.take(future);end=time.perf_counter_ns();self.hud_transfer=dict(ready_before_take=ready,submitted_ns=future.hud_submitted_ns,started_ns=future.hud_started_ns,completed_ns=future.hud_completed_ns,take_begin_ns=begin,take_end_ns=end);self.hud_prefetch.pop(index);self.hud_prefetch_taken+=1;return snapshot
  return HudFrameSnapshot(base,native_library=self.source)
 def close(self):
  if self.closed:return
  try:self.hud_service.close();self.hud_prefetch=[]
  finally:super().close()
method=hud.NativeSourceSession.prepare;source=textwrap.dedent(inspect.getsource(method));old='snapshot=HudFrameSnapshot(owned.frame.base,native_library=self.source)';assert source.count(old)==1
source=source.replace(old,'snapshot=self._take_hud(owned.frame.base)')
source=source.replace('assert not self.closed', "assert not self.closed\n if self.hud_authority is not None and self.hud_authority!=(epoch,generation):raise NativeFrameIdentityError('Retired HUD prepare generation')")
source=source.replace('source_begin=time.perf_counter_ns();hud_profile=None','source_begin=time.perf_counter_ns();hud_profile=None;self.hud_transfer=None')
source=source.replace('return dict(hud_build_split=', 'return dict(bundle_transfer_profile=getattr(self.consumer,"bundle_transfer_profile",None),hud_transfer=self.hud_transfer,hud_prefetch_taken=self.hud_prefetch_taken,hud_build_split=')
ns=dict(method.__globals__);exec(compile(source,'hud-prefetch-prepare','exec'),ns);PrefetchSession.prepare=ns['prepare']
source=dispatch.source
old="elif kind=='prepare':result=session.prepare(owned,e,g,i)";assert source.count(old)==1
source=source.replace(old,old+"\n     elif kind=='hud_prefetch':result=session.prefetch_hud(owned,e,g)")
ns=dict(worker.__dict__);exec(compile(source,'hud-prefetch-worker','exec'),ns);ns['NativeSourceSession']=PrefetchSession
worker.NativeSourceWorker=ns['NativeSourceWorker']
worker.NativeSourceWorker.prefetch_hud=lambda self,bases,epoch=1,generation=1:self._submit('hud_prefetch',bases,epoch,generation,0)
