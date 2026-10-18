import ctypes as C
from pathlib import Path
P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Tail(C.Structure):
 _fields_=[(n,P) for n in ('sky','world','hud','sky_info','sky_copy','hud_info','hud_copy','hud_count','hud_batches','vertices')]+[('nv',U),('vb',Z),('offsets',P),('ob',Z),('ids',P),('ib',Z),('states',P),('nd',U),('sb',Z)]
bridge=C.CDLL(str(Path(__file__).with_name('ordered-render-tail-candidate.dll').resolve()));bridge.nf_ordered_render_tail.argtypes=[C.POINTER(Tail),Z,C.POINTER(U)];bridge.nf_ordered_render_tail.restype=C.c_int
def address(fn):return C.cast(fn,P).value
