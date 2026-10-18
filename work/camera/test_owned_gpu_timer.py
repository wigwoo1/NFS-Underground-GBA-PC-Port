import ctypes as C,json
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());frame=Path(r['wall_diagnostic_frames'][0]['regenerated']).read_bytes()
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_timer_read.argtypes=[C.POINTER(C.c_uint64)]
d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];pixels=C.create_string_buffer(3840*2160*3);expected=None
for cycle in range(3):
 assert d.nf_owned_gpu_draw(frame,len(frame))==0
 assert d.nf_owned_gpu_read(pixels,len(pixels))==0
 if expected is None:expected=pixels.raw
 else:assert pixels.raw==expected
 assert d.nf_owned_gpu_timer_end()==37
 assert d.nf_owned_gpu_timer_begin()==0 and d.nf_owned_gpu_timer_begin()==37
 assert d.nf_owned_gpu_draw(frame,len(frame))==0
 assert d.nf_owned_gpu_timer_end()==0 and d.nf_owned_gpu_timer_end()==37
 assert d.nf_owned_gpu_timer_read(None)==37
 assert d.nf_owned_gpu_finish()==0
 elapsed=C.c_uint64();assert d.nf_owned_gpu_timer_read(C.byref(elapsed))==0 and elapsed.value>0
 assert d.nf_owned_gpu_timer_read(C.byref(elapsed))==37
 assert d.nf_owned_gpu_timer_begin()==0
 assert d.nf_owned_gpu_close()==1
print('PASS timestamp state rejection, elapsed publication, close with active query and three pixel-exact context recreations')
