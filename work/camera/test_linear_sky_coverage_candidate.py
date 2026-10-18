import ctypes as C,json
from pathlib import Path
import numpy as np
root=Path('work/camera');frames=[];checks=[]
for name in ['owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-linear-sky-coverage-transaction-candidate.dll']:
 d=C.CDLL(str((root/name).resolve()));assert d.nf_d3d_open()==0
 try:
  d.nf_d3d_texture.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t]
  d.nf_d3d_sky_pan.argtypes=[C.c_float];d.nf_d3d_draw.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
  sky=C.create_string_buffer(bytes([20,100,200,255])*(240*160))
  for slot in (1001,1002):assert d.nf_d3d_texture(slot,240,160,sky,153600)==0
  assert d.nf_d3d_clear((C.c_float*4)(0,0,0,0))==0;assert d.nf_d3d_sky_pan(.5)==0
  def mask():
   b=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_sky_coverage_read(b,len(b))==0
   return np.frombuffer(b.raw,np.uint8).reshape(2160,3840,4)[:,:,3].copy()
  if 'coverage' in name:
   before=mask();assert before[1000,1000]==255 and before[1000,0]==0
  # Same geometry, sampled triangle interior, translucent foreground.
  vertices=[]
  for x,y in [(20,20),(100,20),(20,100)]:vertices.extend([x,y,0,0,0,1,1,0,0,.5])
  assert d.nf_d3d_draw((C.c_float*30)(*vertices),3,0,0,1,(C.c_float*8)(0,240,160,0,0,0,.5,0),(C.c_int*8)(0,0,3840,2160,300,0,3240,2160))==0
  if 'coverage' in name:
   after=mask();assert after[500,800]==0 and after[1800,3000]==255
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,0))==0;assert not mask().any()
   assert d.nf_d3d_sky_pan(.5)==0
   assert d.nf_d3d_draw((C.c_float*30)(*vertices),3,0,0,1,(C.c_float*8)(0,240,160,0,0,0,.5,0),(C.c_int*8)(0,0,3840,2160,300,0,3240,2160))==0
   checks=['opaque sky marked','outside viewport excluded','translucent foreground excluded','untouched sky retained','frame clear resets coverage']
  out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0;frames.append(out.raw)
 finally:assert d.nf_d3d_close()==0
assert frames[0]==frames[1]
r=dict(result='PASS_ISOLATED_SKY_COVERAGE_COMPONENT',checks=checks,full4k_color_parity=True,scope='Synthetic GPU sky plus blended foreground triangle. No live HUD/discard/route-wide ownership or cadence qualification.')
(root/'prototype-runs/linear-sky-coverage-component-20261010.json').write_text(json.dumps(r,indent=2));print(r)
