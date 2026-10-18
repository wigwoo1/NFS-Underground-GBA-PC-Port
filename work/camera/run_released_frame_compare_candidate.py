"""Isolated native frame comparison releases GIL; ownership and byte checks unchanged."""
import ctypes as C,runpy
from live_owned_gpu_worker import LiveOwnedGPUWorker
original_init=LiveOwnedGPUWorker.__init__
def initialize(self,*args,**kwargs):
 original_init(self,*args,**kwargs)
 self.frame_matches=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t)(C.cast(self.d.nf_owned_frame_matches,C.c_void_p).value)
LiveOwnedGPUWorker.__init__=initialize
runpy.run_path('work/camera/run_road_material_live_candidate.py',run_name='__main__')
