import ctypes as C,hashlib,json
from pathlib import Path
import numpy as np
root=Path('work/camera');runs=[];cases=['background_copy','object_front','owned_text','background_brighten','background_mix','background_disabled']
for name in ['owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-linear-sky-coverage-transaction-candidate.dll']:
 d=C.CDLL(str((root/name).resolve()));assert d.nf_d3d_open()==0;colors=[]
 try:
  d.nf_d3d_texture.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t]
  d.nf_d3d_sky_pan.argtypes=[C.c_float];d.nf_d3d_hud_shader.argtypes=[C.c_void_p,C.c_size_t]
  d.nf_d3d_hud_draw.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
  code=(root/'owned-d3d-hud-effect-candidate.cso').read_bytes();assert d.nf_d3d_hud_shader(code,len(code))==0
  sky=C.create_string_buffer(bytes([20,100,200,255])*(240*160))
  for slot in (1001,1002):assert d.nf_d3d_texture(slot,240,160,sky,153600)==0
  verts=[]
  for x,y in [(0,0),(240,0),(0,160),(240,0),(240,160),(0,160)]:verts.extend([x,y,0,0,0,1,1,1,1,1])
  for case in cases:
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,0))==0;assert d.nf_d3d_sky_pan(.5)==0;assert d.nf_d3d_copy_target(1004)==0
   obj=[200,40,0,255 if case=='object_front' else 0];text=[0,255,0,255 if case=='owned_text' else 0]
   flags=251 if case=='background_disabled' else 255
   for slot,pixel in [(1,obj),(2,[0,0,flags,255]),(3,text)]:
    buf=C.create_string_buffer(bytes(pixel)*(240*160));assert d.nf_d3d_texture(slot,240,160,buf,153600)==0
   params=(C.c_float*24)();params[7]=1;params[16]=16
   if case=='owned_text':C.cast(params,C.POINTER(C.c_int))[20]=1
   if case=='background_brighten':params[4]=2;params[9]=1;params[18]=8
   if case=='background_mix':params[4]=1;params[9]=1;params[14]=1;params[16]=8;params[17]=8
   assert d.nf_d3d_hud_draw((C.c_float*60)(*verts),6,(C.c_uint*4)(1,2,1004,3),params,(C.c_float*8)(0,240,160,0,0,0,.5,0),(C.c_int*8)(0,0,3840,2160,300,0,3240,2160))==0
   buf=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(buf,len(buf))==0;colors.append(hashlib.sha256(buf.raw).hexdigest())
   if 'coverage' in name:
    assert d.nf_d3d_sky_coverage_read(buf,len(buf))==0
    alpha=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)[1000,1000,3]
    assert alpha==(255 if case=='background_copy' else 0),(case,int(alpha))
  runs.append(colors)
 finally:assert d.nf_d3d_close()==0
assert runs[0]==runs[1]
r=dict(result='PASS_GPU_HUD_SKY_COVERAGE_BRANCHES',cases=cases,full4k_color_parity=True,scope='Six synthetic actual HUD shader cases. Captured-scene parity and additional depth/effect edge cases remain required; no live cadence proof.')
(root/'prototype-runs/linear-sky-hud-coverage-branches-20261010.json').write_text(json.dumps(r,indent=2));print(r)
