import ctypes as C,json,statistics,time
from pathlib import Path
import numpy as np
p=Path(__file__).parent;d=C.CDLL(str((p/'owned-d3d-texture-backdrop-candidate.dll').resolve()));P=C.c_void_p
d.nf_d3d_open.restype=C.c_int;d.nf_d3d_close.restype=C.c_int;d.nf_d3d_clear.argtypes=[P];d.nf_d3d_backdrop.argtypes=[P,C.c_size_t];d.nf_d3d_backdrop_texture.argtypes=[P,C.c_size_t];d.nf_d3d_read.argtypes=[P,C.c_size_t]
assert d.nf_d3d_open()==0
rng=np.random.default_rng(33211); rows=rng.integers(0,256,(160,4),dtype=np.uint8); timings={'runs':[],'texture':[]};orders=[]
try:
 for label,fn in [('runs',d.nf_d3d_backdrop),('texture',d.nf_d3d_backdrop_texture)]:
  assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0;assert fn(rows.ctypes.data,rows.nbytes)==0
  image=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(image,len(image))==0
 for repeat in range(6):
  order=['runs','texture'] if repeat%2==0 else ['texture','runs'];orders.append(order)
  for label in order:
   assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0
   fn=d.nf_d3d_backdrop if label=='runs' else d.nf_d3d_backdrop_texture
   batch=[]
   for j in range(6):
    rows[:,0]=((rows[:,0].astype(np.uint16)+(j+repeat+1))%256).astype(np.uint8)
    t=time.perf_counter_ns();assert fn(rows.ctypes.data,rows.nbytes)==0;batch.append(time.perf_counter_ns()-t)
   timings[label].extend(batch)
   image=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(image,len(image))==0
finally:assert d.nf_d3d_close()==0
summary={k:{'n':len(v),'median_us':statistics.median(v)/1000,'p95_us':float(np.percentile(v,95))/1000,'max_us':max(v)/1000,'mean_us':statistics.mean(v)/1000} for k,v in timings.items()}
out={'result':'PASS_TEXTURE_BACKDROP_CPU_SUBMISSION_MICROPROFILE','orders':orders,'summary':summary,'scope':'Isolated Python-call-to-D3D immediate-context return intervals for source backdrop methods, with readback fences outside the timed intervals. This is not GPU execution time, live game pacing, or a promotion result.'}
(p/'prototype-runs'/'d3d-texture-backdrop-microprofile.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
