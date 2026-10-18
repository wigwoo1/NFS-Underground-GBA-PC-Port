import ctypes as C,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-texture-update-candidate.dll').resolve()));P=C.c_void_p
d.nf_d3d_texture.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_texture_resource_stats.argtypes=[P];d.nf_d3d_stats.argtypes=[P]
assert d.nf_d3d_open()==0
def stats():
 x=(C.c_uint64*2)();assert d.nf_d3d_texture_resource_stats(x)==0;return list(x)
try:
 red=C.create_string_buffer(bytes([255,0,0,255])*4);blue=C.create_string_buffer(bytes([0,0,255,255])*4);large=C.create_string_buffer(bytes([0,255,0,255])*9)
 assert d.nf_d3d_texture(1,2,2,red,16)==0;assert stats()==[1,0]
 assert d.nf_d3d_texture(1,2,2,blue,16)==0;assert stats()==[1,1]
 assert d.nf_d3d_texture(1,3,3,large,36)==0;assert stats()==[2,1]
 assert d.nf_d3d_texture(1,3,3,large,35)==1;assert stats()==[2,1]
 wrong=[];t=threading.Thread(target=lambda:wrong.append(d.nf_d3d_texture(1,3,3,large,36)));t.start();t.join();assert wrong==[1];assert stats()==[2,1]
finally:assert d.nf_d3d_close()==0
live=(C.c_uint64*4)();assert d.nf_d3d_stats(live)==0;assert live[2]==0
out=dict(result='PASS_TEXTURE_UPDATE_RESIZE_SIZE_OWNER_CLEANUP',creates=2,updates=1,live_after_close=int(live[2]),scope='Resource branch and ownership checks; scene pixel parity verified separately.')
(p/'prototype-runs/native-texture-update-resource-20261008.json').write_text(json.dumps(out,indent=2));print(out)
