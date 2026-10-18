import ctypes as C,json
from pathlib import Path
import numpy as np
root=Path('work/camera');frames=[];checks=[]
for name in ['owned-d3d-world-stream-linear-transaction-candidate.dll','owned-d3d-async-sky-coverage-transaction-candidate.dll']:
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
   d.nf_d3d_async_coverage_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint]
   d.nf_d3d_async_skyband_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t]
   assert d.nf_d3d_async_coverage_capture(12,7,480)==1
   assert d.nf_d3d_async_coverage_capture(11,0,480)==1
   assert d.nf_d3d_async_coverage_capture(11,7,2097)==1
   assert d.nf_d3d_async_coverage_capture(11,7,480)==0
   assert d.nf_d3d_async_coverage_capture(11,8,480)==1
   band=C.create_string_buffer(3240*64*4)
   assert d.nf_d3d_async_skyband_poll(11,8,band,len(band))==1
   assert d.nf_d3d_async_skyband_poll(11,7,band,len(band)-1)==1
   # Full synchronous diagnostic read above has already flushed GPU work;
   # explicitly flush then wait with bounded nonblocking polling.
   import time
   deadline=time.monotonic()+5
   while True:
    rc=d.nf_d3d_async_skyband_poll(11,7,band,len(band))
    assert rc in (0,3)
    if rc==0:break
    assert time.monotonic()<deadline
    time.sleep(.001)
   assert np.array_equal(np.frombuffer(band.raw,np.uint8).reshape(64,3240,4)[:,:,3],after[480:544,300:3540])
   assert d.nf_d3d_async_skyband_poll(11,7,band,len(band))==1

   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,0))==0;assert not mask().any()
   assert d.nf_d3d_sky_pan(.5)==0
   assert d.nf_d3d_draw((C.c_float*30)(*vertices),3,0,0,1,(C.c_float*8)(0,240,160,0,0,0,.5,0),(C.c_int*8)(0,0,3840,2160,300,0,3240,2160))==0
   checks=['opaque sky marked','outside viewport excluded','translucent foreground excluded','untouched sky retained','frame clear resets coverage','async band alpha exact synchronous crop','invalid slot/zero identity/y rejected','pending overwrite rejected','wrong owner identity/size rejected','consumed slot rejects duplicate poll']
  out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0;frames.append(out.raw)
 finally:assert d.nf_d3d_close()==0
assert frames[0]==frames[1]
r=dict(result='PASS_ASYNC_SKY_COVERAGE_COMPONENT',checks=checks,full4k_color_parity=True,scope='Synthetic GPU sky/foreground plus nonblocking band readback and ownership guards. Color parity exact; no live cadence qualification.')
(root/'prototype-runs/async-sky-coverage-component-20261010.json').write_text(json.dumps(r,indent=2));print(r)


