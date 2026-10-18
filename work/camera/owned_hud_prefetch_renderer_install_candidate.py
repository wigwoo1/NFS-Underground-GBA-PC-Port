"""Experimental bounded immutable HUD prefetch; native renderer remains single-threaded."""
import inspect,textwrap
import owned_native_source_segmented_release_worker_candidate as worker
import owned_renderer_dispatch_trace_install_candidate as dispatch
import owned_native_source_hud_cache_lease_session_candidate as hud
from owned_hud_preparation_service_candidate import HudPreparationService
from owned_hud_shared_library_binding_candidate import HudFrameSnapshot
Base=worker.NativeSourceSession
class PrefetchSession(Base):
 def __init__(self):
  super().__init__();self.hud_service=HudPreparationService(self.source);self.hud_prefetch=[];self.hud_prefetch_taken=0
 def prefetch_hud(self,bases):
  if self.closed:raise RuntimeError('Closed HUD prefetch')
  if type(bases) is not tuple or len(bases)>2 or any(type(x) is not bytes for x in bases):raise ValueError('Bounded immutable endpoint pair required')
  for base,future in self.hud_prefetch:
   if not any(base is x for x in bases):self.hud_service.take(future).close()
  self.hud_prefetch=[(base,future) for base,future in self.hud_prefetch if any(base is x for x in bases)]
  for base in bases:
   if not any(x._base is base for x in self.hud_snapshots) and not any(x is base for x,f in self.hud_prefetch):self.hud_prefetch.append((base,self.hud_service.submit(base)))
  return dict(prefetch_count=len(self.hud_prefetch))
 def _take_hud(self,base):
  for index,(retained,future) in enumerate(self.hud_prefetch):
   if retained is base:
    snapshot=self.hud_service.take(future);self.hud_prefetch.pop(index);self.hud_prefetch_taken+=1;return snapshot
  return HudFrameSnapshot(base,native_library=self.source)
 def close(self):
  if self.closed:return
  try:self.hud_service.close();self.hud_prefetch=[]
  finally:super().close()
method=hud.NativeSourceSession.prepare;source=textwrap.dedent(inspect.getsource(method));old='snapshot=HudFrameSnapshot(owned.frame.base,native_library=self.source)';assert source.count(old)==1
source=source.replace(old,'snapshot=self._take_hud(owned.frame.base)')
source=source.replace('return dict(hud_build_split=', 'return dict(hud_prefetch_taken=self.hud_prefetch_taken,hud_build_split=')
ns=dict(method.__globals__);exec(compile(source,'hud-prefetch-prepare','exec'),ns);PrefetchSession.prepare=ns['prepare']
source=dispatch.source
old="elif kind=='prepare':result=session.prepare(owned,e,g,i)";assert source.count(old)==1
source=source.replace(old,old+"\n     elif kind=='hud_prefetch':result=session.prefetch_hud(owned)")
ns=dict(worker.__dict__);exec(compile(source,'hud-prefetch-worker','exec'),ns);ns['NativeSourceSession']=PrefetchSession
worker.NativeSourceWorker=ns['NativeSourceWorker']
worker.NativeSourceWorker.prefetch_hud=lambda self,bases:self._submit('hud_prefetch',bases,0,0,0)
