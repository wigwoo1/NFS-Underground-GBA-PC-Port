"""Real 4K pixel parity for exact repeats, changed texels, dimensions and slot reuse."""
import ctypes as C,json,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).parent
v=np.asarray([[x,y,u,v,0,1,1,1,1,1] for x,y,u,v in [(0,0,0,0),(3840,0,1,0),(0,2160,0,1),(3840,0,1,0),(3840,2160,1,1),(0,2160,0,1)]],np.float32)
config=(C.c_float*8)(0,3840,2160,0,1,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,0,0,3840,2160)
fixtures=[]
for w,h,seed in [(2,2,1),(2,2,1),(2,2,7),(3,2,9),(3,2,12),(2,2,1),(2,2,22)]:
 rng=np.random.default_rng(seed);pixels=rng.integers(0,256,(h,w,4),dtype=np.uint8);pixels[:,:,3]=255;fixtures.append((w,h,pixels.tobytes()))
def run(name):
 d=C.CDLL(str((P/name).resolve()));d.nf_d3d_texture_cached.argtypes=[C.c_uint]*3+[C.c_void_p,C.c_size_t];d.nf_d3d_draw.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
 assert d.nf_d3d_open()==0;hashes=[]
 try:
  for w,h,pixels in fixtures:
   buf=C.create_string_buffer(pixels);assert d.nf_d3d_texture_cached(1,w,h,buf,len(pixels))==0
   assert d.nf_d3d_draw(v.ctypes.data,6,1,0,0,config,rect)==0
   out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0
   actual=np.frombuffer(out,np.uint8).reshape(2160,3840,4)
   expected=np.frombuffer(pixels,np.uint8).reshape(h,w,4)[np.minimum((np.arange(2160)+.5)*h/2160,h-1).astype(int)[:,None],np.minimum((np.arange(3840)+.5)*w/3840,w-1).astype(int)[None,:]]
   assert np.array_equal(actual,expected),(name,w,h)
   hashes.append(hashlib.sha256(out.raw).hexdigest())
  stats=(C.c_uint64*3)();assert d.nf_d3d_texture_cache_stats(stats)==0;assert list(stats)==[6,1,16]
  reused=None
  if hasattr(d,'nf_d3d_resource_reuse_count'):
   d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=d.nf_d3d_resource_reuse_count();assert reused==3,reused
 finally:assert d.nf_d3d_close()==0
 assert d.nf_d3d_texture_cache_stats(stats)==0 and stats[2]==0
 return dict(hashes=hashes,resource_reuses=reused,closed_cache_empty=True)
a=run('owned-d3d-sky-three-stage-transaction-candidate.dll');b=run('owned-d3d-texture-resource-reuse-candidate.dll');assert a['hashes']==b['hashes']
result=dict(result='PASS_REAL_4K_TEXTURE_RESOURCE_REUSE_PARITY',frames=7,baseline=a,candidate=b,scope='Every 4K RGBA pixel versus independent nearest-texel oracle and unchanged baseline; three actual resource updates, one exact cache hit, dimensions and reverted content. Component only; no live fullscene cadence proof.')
(P/'prototype-runs/texture-resource-reuse-parity-20261009.json').write_text(json.dumps(result,indent=2));print(result['result'])
