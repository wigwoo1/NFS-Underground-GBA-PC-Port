"""Bounded observed HUD ownership at existing session boundaries."""
import ctypes as C
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
summary=dict(observations=0,max_observed_owners=0,max_observed_bytes=0,max_observed_refs=0,max_pending=0,max_snapshots=0,closed_sessions=0)
def observe(session):
 values=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(values)==1
 summary['observations']+=1
 for key,value in zip(('max_observed_owners','max_observed_bytes','max_observed_refs'),values):summary[key]=max(summary[key],value)
 summary['max_pending']=max(summary['max_pending'],len(session.hud_prefetch));summary['max_snapshots']=max(summary['max_snapshots'],len(session.hud_snapshots))
 assert len(session.hud_prefetch)<=2 and len(session.hud_snapshots)<=2
for name in ('prefetch_hud','_take_hud'):
 original=getattr(PrefetchSession,name)
 def wrapped(self,*args,_original=original,**kwargs):
  result=_original(self,*args,**kwargs);observe(self);return result
 setattr(PrefetchSession,name,wrapped)
original_close=PrefetchSession.close
def close(self):
 was_closed=self.closed;result=original_close(self)
 if not was_closed:
  values=(C.c_uint64*3)();assert self.source.nf_hud_owner_stats(values)==1 and list(values)==[0,0,0];summary['closed_sessions']+=1;summary['final_native_stats']=list(values)
 return result
PrefetchSession.close=close
