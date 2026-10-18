"""Default-off short HUD lease release; immutable creator must remain open."""
import ctypes as C,os
from owned_hud_shared_library_binding_candidate import HudFrameLease
Release=C.PYFUNCTYPE(C.c_int,C.c_uint64,C.c_uint64)
original_init=HudFrameLease.__init__
original_close=HudFrameLease.close
stats={'selected_leases':0,'short_releases':0,'closed_owner_fallbacks':0}
def init(self,owner,frame):
 original_init(self,owner,frame)
 if os.environ.get('NFSUG_HUD_LEASE_RELEASE_KEEP_GIL')=='1':
  if not hasattr(owner,'_short_release_thunk'):
   owner._short_release_thunk=Release(C.cast(owner.d.nf_hud_owner_release,C.c_void_p).value)
  self._short_release_owner=owner
  stats['selected_leases']+=1
def close(self):
 if self.closed:return
 owner=getattr(self,'_short_release_owner',None)
 if owner is not None and not owner.closed:
  assert owner._short_release_thunk(self.token,self.epoch)
  self.closed=True;self.frame=None;self._short_release_owner=None
  stats['short_releases']+=1
 else:
  if owner is not None:stats['closed_owner_fallbacks']+=1
  original_close(self)
  self._short_release_owner=None
HudFrameLease.__init__=init
HudFrameLease.close=close
