"""GPU coverage guards for source alpha discard and scissor, with color parity."""
import ctypes as C,json,hashlib
from pathlib import Path
import numpy as np
root=Path('work/camera');runs=[]
for name in ['owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-linear-sky-coverage-transaction-candidate.dll']:
 d=C.CDLL(str((root/name).resolve()));assert d.nf_d3d_open()==0
 outputs=[]
 try:
  d.nf_d3d_texture.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t]
  d.nf_d3d_sky_pan.argtypes=[C.c_float];d.nf_d3d_draw.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
  sky=C.create_string_buffer(bytes([20,100,200,255])*(240*160))
  for slot in (1001,1002):assert d.nf_d3d_texture(slot,240,160,sky,153600)==0
  verts=[]
  for x,y in [(20,20),(100,20),(20,100)]:verts.extend([x,y,.5,.5,0,1,1,1,1,1])
  def draw(alpha,scissor):
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,0))==0;assert d.nf_d3d_sky_pan(.25)==0
   pixel=C.create_string_buffer(bytes([200,0,0,alpha]));assert d.nf_d3d_texture(1,1,1,pixel,4)==0
   assert d.nf_d3d_draw((C.c_float*30)(*verts),3,1,0,0,(C.c_float*8)(0,240,160,0,1,1,.5,0),(C.c_int*8)(*scissor))==0
   b=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(b,len(b))==0;outputs.append(hashlib.sha256(b.raw).hexdigest())
   if 'coverage' in name:
    assert d.nf_d3d_sky_coverage_read(b,len(b))==0
    return np.frombuffer(b.raw,np.uint8).reshape(2160,3840,4)[:,:,3].copy()
  full=(0,0,3840,2160,300,0,3240,2160)
  for alpha in (0,127):
   mask=draw(alpha,full)
   if mask is not None:assert mask[500,800]==255,'discarded foreground must preserve sky'
  mask=draw(128,full)
  if mask is not None:assert mask[500,800]==0,'above-threshold foreground must exclude sky'
  mask=draw(255,(700,0,900,2160,300,0,3240,2160))
  if mask is not None:
   assert mask[500,800]==0 and mask[500,950]==255,'scissor must constrain mask updates'
  runs.append(outputs)
 finally:assert d.nf_d3d_close()==0
assert runs[0]==runs[1]
r=dict(result='PASS_SKY_COVERAGE_DISCARD_SCISSOR',cases=4,full4k_color_parity=True,alpha_cases=[0,127,128,255],scope='Actual GPU sampled foreground shader with discard threshold0.5 and scissor. Live HUD/background sampling and cadence remain unverified.')
(root/'prototype-runs/linear-sky-coverage-discard-scissor-20261010.json').write_text(json.dumps(r,indent=2));print(r)
