import ctypes as C, numpy as np, hashlib,json
from pathlib import Path
from owned_source_d3d_backdrop_batch_consumer_candidate import OwnedD3DConsumer
c=OwnedD3DConsumer();d=c.d;results=[]
def quad(h):return np.asarray([[x,y,u,v,0,1,1,1,1,1] for x,y,u,v in [(0,0,0,0),(240,0,1,0),(0,h,0,1),(240,0,1,0),(240,h,1,1),(0,h,0,1)]],np.float32)
config=(C.c_float*8)(0,240,160,0,0,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160)
try:
 for label,colors in [('solid',np.tile([17,37,91,255],(160,1)).astype(np.uint8)),('alternating',np.asarray([[255 if y%2 else 0,37,y,255] for y in range(160)],np.uint8)),('bands',np.asarray([[y//7*9,y//11*13,y//17*21,255] for y in range(160)],np.uint8))]:
  images=[]
  starts=np.concatenate(([0],np.flatnonzero(np.any(colors[1:]!=colors[:-1],axis=1))+1));ends=np.concatenate((starts[1:],[160]))
  for batched in (False,True):
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0
   vertices=[]
   for a,b in zip(starts,ends):
    v=quad(b-a);v[:,1]+=a;v[:,6:10]=colors[a].astype(np.float32)/255
    if batched:vertices.append(v)
    else:assert d.nf_d3d_draw(v.ctypes.data,6,0,0,0,config,rect)==0
   if batched:
    v=np.concatenate(vertices);assert d.nf_d3d_draw(v.ctypes.data,len(v),0,0,0,config,rect)==0
   buf=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(buf,len(buf))==0;images.append(buf.raw)
  assert images[0]==images[1],label
  results.append(dict(pattern=label,bands=len(starts),rgba_sha256=hashlib.sha256(images[0]).hexdigest()))
finally:c.close()
out=dict(result='PASS_BACKDROP_BAND_GPU_PARITY',checks=results,scope='Full 4K native RGBA target exact comparison of old per-band draws and one combined ordered triangle list; no live timing or visibility proof.')
Path('work/camera/prototype-runs/native-backdrop-band-pixels.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
