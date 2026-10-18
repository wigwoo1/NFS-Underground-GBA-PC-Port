import ctypes as C, hashlib, json
from pathlib import Path
import numpy as np
p=Path(__file__).parent
d=C.CDLL(str((p/'owned-d3d-texture-backdrop-candidate.dll').resolve()))
P=C.c_void_p
d.nf_d3d_open.restype=C.c_int
d.nf_d3d_close.restype=C.c_int
d.nf_d3d_clear.argtypes=[P]
d.nf_d3d_backdrop.argtypes=[P,C.c_size_t]
d.nf_d3d_backdrop_texture.argtypes=[P,C.c_size_t]
d.nf_d3d_read.argtypes=[P,C.c_size_t]
d.nf_d3d_stats.argtypes=[P]
patterns=[]
patterns.append(('solid',np.tile(np.array([17,37,91,255],np.uint8),(160,1))))
patterns.append(('alternating',np.array([[255 if y%2 else 0,(y*29)%256,y,(y*7)%256] for y in range(160)],np.uint8)))
patterns.append(('bands',np.array([[y//7*9,y//11*13,y//17*21,255 if y%3 else 128] for y in range(160)],np.uint8)))
patterns.append(('unique_rows',np.array([[y,(y*73+19)%256,(y*151+3)%256,255] for y in range(160)],np.uint8)))
rng=np.random.default_rng(8492);patterns.append(('random_rows',rng.integers(0,256,(160,4),dtype=np.uint8)))
assert d.nf_d3d_open()==0
results=[]
try:
 for label,rows in patterns:
  images=[]
  for name,fn in [('runs',d.nf_d3d_backdrop),('texture',d.nf_d3d_backdrop_texture)]:
   clear=(C.c_float*4)(.03125,.125,.375,1)
   assert d.nf_d3d_clear(clear)==0
   assert fn(rows.ctypes.data,rows.nbytes)==0,(label,name)
   image=C.create_string_buffer(3840*2160*4)
   assert d.nf_d3d_read(image,len(image))==0
   images.append(image.raw)
  same=images[0]==images[1]
  if not same:
   diffs=[i for i,(a,b) in enumerate(zip(*images)) if a!=b]
   first=diffs[0]; coords=[(q//4%3840,q//4//3840,images[0][q:q+4].hex(),images[1][q:q+4].hex()) for q in diffs[:5]]
   samples=[(y,images[0][(y*3840+800)*4:(y*3840+800)*4+4].hex(),images[1][(y*3840+800)*4:(y*3840+800)*4+4].hex()) for y in (0,12,13,14,26,27,40,41,54,55,67,68,80,81,100,101,2158,2159)]
   raise AssertionError((label,'mismatch_bytes',len(diffs),'xy_baseline_texture',coords))
  results.append({'pattern':label,'sha256':hashlib.sha256(images[0]).hexdigest(),'equal_rgba_bytes':len(images[0])})
 before=(C.c_uint64*4)();after=(C.c_uint64*4)()
 assert d.nf_d3d_stats(before)==0
 invalid_rows=np.zeros((160,4),np.uint8)
 assert d.nf_d3d_backdrop_texture(invalid_rows.ctypes.data,639)==1
 assert d.nf_d3d_backdrop_texture(None,640)==1
 assert d.nf_d3d_stats(after)==0 and list(before)==list(after),(list(before),list(after))
finally:
 assert d.nf_d3d_close()==0
out={'result':'PASS_D3D_TEXTURE_BACKDROP_4K_RGBA_PARITY','patterns':results,'invalid_input_guards':'PASS_NO_RENDERER_STATE_CHANGE','scope':'Isolated 3840x2160 RGBA renderer component comparison between existing run-compressed backdrop draws and a reusable 1x160 texture updated per backdrop. Does not measure live frame pacing or establish a performance improvement.'}
(p/'prototype-runs'/'d3d-texture-backdrop-parity.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
