import ctypes as C
import owned_hud_target_reuse_backend_install_candidate
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.render
Ticks=C.c_uint64*12
def render(self,*args,**kwargs):
 result=original(self,*args,**kwargs)
 ticks=Ticks();assert self.d.nf_d3d_hud_phase_ticks(ticks,C.sizeof(ticks))==0
 rows=[s for s in self.stage_profile if s['stage']=='ordered_sky_world_hud'];assert len(rows)==1
 rows[0]['native_hud_ticks']=list(ticks)
 return result
OwnedD3DConsumer.render=render
