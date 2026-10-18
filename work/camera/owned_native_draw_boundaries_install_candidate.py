"""Retain existing native input/draw callback boundaries; no DLL mutation."""
import ctypes as C
import owned_source_packet_phase_profile_install_candidate as current
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
U=C.c_uint64
def read_draw_boundaries(d):
 values=(U*4)();d.nf_owned_gpu_callback_profile.argtypes=[C.POINTER(U)];d.nf_owned_gpu_callback_profile.restype=C.c_int
 if d.nf_owned_gpu_callback_profile(values)!=0:raise RuntimeError('Native draw boundary read rejected')
 result=list(values)
 if not all(result[i]<=result[i+1] for i in range(3)):raise RuntimeError('Native draw boundaries invalid')
 return result
source=current.source
needle='source_packet_stages=read_packet_stages(s),'
assert source.count(needle)==1
source=source.replace(needle,needle+'native_draw_boundaries=read_draw_boundaries(s),')
ns=dict(PrefetchSession.prepare.__globals__,read_draw_boundaries=read_draw_boundaries)
exec(compile(source,'native-input-draw-boundaries','exec'),ns)
PrefetchSession.prepare=ns['prepare']
