import ctypes as C,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-material-batch-candidate.dll').resolve()));P=C.c_void_p
d.nf_d3d_material_packet_cached.argtypes=[P,C.c_size_t,P,C.c_uint,C.c_size_t];d.nf_d3d_texture_cache_stats.argtypes=[P];assert d.nf_d3d_open()==0
def stats():
 x=(C.c_uint64*3)();assert d.nf_d3d_texture_cache_stats(x)==0;return list(x)
rgba=C.create_string_buffer(bytes([255,0,0,255])*4+bytes([0,0,255,255])*4);records=(C.c_uint*8)(2,2,0,16,2,2,16,16)
try:
 assert d.nf_d3d_material_packet_cached(rgba,32,records,2,32)==0;assert stats()==[2,0,32]
 assert d.nf_d3d_material_packet_cached(rgba,32,records,2,32)==0;assert stats()==[2,2,32]
 for i in range(200):
  rgba[0]=bytes([i%2]);assert d.nf_d3d_material_packet_cached(rgba,32,records,2,32)==0;assert stats()[2]==32
 before=stats();records[6]=33;rgba[0]=b'\x7f';assert d.nf_d3d_material_packet_cached(rgba,32,records,2,32)==1;assert stats()==before;records[6]=16
 assert d.nf_d3d_material_packet_cached(rgba,32,records,65,1040)==1;assert stats()==before
 wrong=[];t=threading.Thread(target=lambda:wrong.append(d.nf_d3d_material_packet_cached(rgba,32,records,2,32)));t.start();t.join();assert wrong==[1];assert stats()==before
finally:assert d.nf_d3d_close()==0
assert stats()[2]==0
out=dict(result='PASS_MATERIAL_PACKET_ATOMIC_VALIDATION_CACHE_REPLACEMENT_OWNER_CLEANUP',replacement_cycles=200,retained_bytes_before_close=32,retained_bytes_after_close=stats()[2],scope='Prevalidation is atomic for malformed packets, not rollback after GPU allocation failure. Pixel fidelity verified separately.')
(p/'prototype-runs/native-material-batch-guards-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
