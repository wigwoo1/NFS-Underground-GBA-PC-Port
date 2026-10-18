"""Actual dynamic resource growth, whole-packet guards and close/reopen ownership."""
import ctypes as C,json,numpy as np
from pathlib import Path
p=Path(__file__).parent;d=C.CDLL(str((p/'owned-d3d-world-stream-transaction-candidate.dll').resolve()));P=C.c_void_p;S=C.c_size_t;U=C.c_uint
d.nf_d3d_world_batch.argtypes=[P,U,S,P,S,P,S,P,U,S];d.nf_d3d_read.argtypes=[P,S];d.nf_d3d_world_stream_stats.argtypes=[P,S];d.nf_d3d_clear.argtypes=[P]
def state():
 x=(C.c_uint64*3)();assert d.nf_d3d_world_stream_stats(x,24)==0;return list(x)
checks=[]
for epoch in range(2):
 assert d.nf_d3d_open()==0;assert state()==[0,0,0]
 try:
  for n in [6,120,600,6,65532,6]:
   v=np.zeros((n,10),np.float32);v[:,0:2]=-100;v[:,5:10]=1
   offsets=(U*2)(0,n);ids=(U*1)(0);cfg=(C.c_float*8)(0,3840,2160,0,0,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,0,0,3840,2160);mode=(U*2)(0,0);raw=C.create_string_buffer(bytes(cfg)+bytes(rect)+bytes(mode));assert len(raw.raw)>=72
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0
   assert d.nf_d3d_world_batch(v.ctypes.data,n,v.nbytes,offsets,8,ids,4,raw,1,72)==0
   st=state();assert st[1:]==[1,0] and n*40<=st[0]<=4194304
   before=(C.c_uint64*4)();after=(C.c_uint64*4)();assert d.nf_d3d_stats(before)==0
   # Invalid final draw mode must reject before allocating/mapping/drawing anything.
   bad=C.create_string_buffer(bytes(raw)[:72]);C.cast(C.addressof(bad)+64,C.POINTER(U))[0]=4
   assert d.nf_d3d_world_batch(v.ctypes.data,n,v.nbytes,offsets,8,ids,4,bad,1,72)==1
   assert d.nf_d3d_world_batch(v.ctypes.data,n,v.nbytes-1,offsets,8,ids,4,raw,1,72)==1
   assert state()==st;assert d.nf_d3d_stats(after)==0 and list(before)==list(after)
   image=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(image,len(image))==0;a=np.frombuffer(image,np.uint8).reshape(-1,4);assert np.all(a[:,:3]==0) and np.all(a[:,3]==255)
   checks.append(dict(epoch=epoch,vertices=n,capacity=st[0]))
 finally:assert d.nf_d3d_close()==0
 assert state()==[0,0,0]
out=dict(result='PASS_GPU_WORLD_STREAM_GROWTH_GUARDS_TEARDOWN',checks=checks,scope='Real GPU growth through4MB, shrink reuse, invalid byte/mode rejection with unchanged counters/capacity and exact4K clear pixels; two initialize/close epochs. Degenerate offscreen guard fixtures, not scene-motion/cadence proof.')
(p/'prototype-runs/world-stream-growth-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
