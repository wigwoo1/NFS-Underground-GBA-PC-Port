import ctypes as C,json,time,threading
from pathlib import Path
import numpy as np
d=C.CDLL(str(Path('work/camera/owned-d3d-async-skyband-candidate.dll').resolve()))
d.nf_d3d_clear.argtypes=[C.c_void_p];d.nf_d3d_async_skyband_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint];d.nf_d3d_async_skyband_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];d.nf_d3d_async_stats.argtypes=[C.c_void_p]
size=3240*64*4;buffer=C.create_string_buffer(size);stats=(C.c_uint*2)();assert d.nf_d3d_open()==0;checks=0;polls=[]
try:
 assert d.nf_d3d_async_skyband_capture(3,1,648)==1;checks+=1
 assert d.nf_d3d_async_skyband_capture(0,1,2160-63)==1;checks+=1
 colors=[(1,0,0,1),(0,1,0,1),(0,0,1,1)]
 for slot,(color,y) in enumerate(zip(colors,[648,864,1296])):
  assert d.nf_d3d_clear((C.c_float*4)(*color))==0
  assert d.nf_d3d_async_skyband_capture(slot,slot+11,y)==0
  assert d.nf_d3d_async_skyband_capture(slot,slot+20,y)==1;checks+=1
 assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[3,3]
 assert d.nf_d3d_async_skyband_poll(0,999,buffer,size)==1;checks+=1
 assert d.nf_d3d_async_skyband_poll(0,11,buffer,size-4)==1;checks+=1
 worker_result=[];thread=threading.Thread(target=lambda:worker_result.append(d.nf_d3d_async_skyband_poll(0,11,buffer,size)));thread.start();thread.join();assert worker_result==[1];checks+=1
 for slot,color in enumerate(colors):
  deadline=time.perf_counter()+2;tries=0
  while True:
   rc=d.nf_d3d_async_skyband_poll(slot,slot+11,buffer,size);tries+=1
   assert rc in (0,3)
   if rc==0:break
   assert time.perf_counter()<deadline;time.sleep(.001)
  pixels=np.frombuffer(buffer.raw,np.uint8).reshape(64,3240,4);assert np.all(pixels==np.array(color,dtype=np.uint8)*255)
  polls.append(dict(slot=slot,attempts=tries,exact_pixels=3240*64))
  assert d.nf_d3d_async_skyband_poll(slot,slot+11,buffer,size)==1;checks+=1
 assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[3,0]
 assert d.nf_d3d_async_skyband_capture(0,99,1440)==0
finally:
 assert d.nf_d3d_close()==0
assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[0,0]
assert d.nf_d3d_open()==0;assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[0,0];assert d.nf_d3d_close()==0
out=dict(result='PASS_ASYNC_SKYBAND_OWNERSHIP_PIXELS_CLEANUP',negative_checks=checks,polls=polls,slots=3,bytes_per_slot=size,scope='Actual D3D colored-target copy/readback per slot, nonblocking poll API, wrongidentity/owner/extent/busy guards and pending-close/reopen cleanup. Does not measure live cadence or source scene fidelity.')
Path('work/camera/prototype-runs/async-skyband-lifecycle-20261009.json').write_text(json.dumps(out,indent=2));print(out)
