import ctypes as C,json,time,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-async-crop-candidate.dll').resolve()));g=C.WinDLL('opengl32')
d.nf_crop_enqueue.argtypes=[C.c_uint64,C.c_uint,C.c_uint];d.nf_crop_poll.argtypes=[C.POINTER(C.c_uint64),C.c_void_p,C.c_size_t]
g.glClearColor.argtypes=[C.c_float]*4;g.glClear.argtypes=[C.c_uint];g.glPixelStorei.argtypes=[C.c_uint,C.c_int];g.glGetIntegerv.argtypes=[C.c_uint,C.POINTER(C.c_int)]
b=C.create_string_buffer(3072);identity=C.c_uint64();checks=[]
assert d.nf_owned_gpu_window(0)==0
try:
 assert d.nf_crop_poll(C.byref(identity),b,3072)==2
 assert d.nf_crop_enqueue(0,0,0)==37 and d.nf_crop_enqueue(1,3777,0)==37
 g.glPixelStorei(0x0d05,8);g.glPixelStorei(0x0d02,80);g.glPixelStorei(0x0d04,3);g.glPixelStorei(0x0d03,2)
 for i,color in enumerate(((1,0,0),(0,1,0),(0,0,1)),1):
  g.glClearColor(*color,1);g.glClear(0x4000)
  assert d.nf_crop_enqueue(i,300,600)==0
  for key,expected in ((0x0d05,8),(0x0d02,80),(0x0d04,3),(0x0d03,2)):
   v=C.c_int();g.glGetIntegerv(key,C.byref(v));assert v.value==expected
 assert d.nf_crop_pending()==3 and d.nf_crop_enqueue(4,300,600)==2
 assert d.nf_crop_poll(C.byref(identity),b,3071)==37 and d.nf_crop_pending()==3
 other=[];t=threading.Thread(target=lambda:other.append(d.nf_crop_pending()));t.start();t.join();assert other==[-1]
 for i,color in enumerate(((255,0,0),(0,255,0),(0,0,255)),1):
  end=time.perf_counter()+5;polls=0
  while True:
   rc=d.nf_crop_poll(C.byref(identity),b,3072);polls+=1
   if rc!=0:break
   assert time.perf_counter()<end;time.sleep(.001)
  assert rc==1 and identity.value==i and b.raw==bytes(color)*1024
  checks.append(dict(id=i,polls=polls,rgb=list(color)))
 assert d.nf_crop_pending()==0
 assert d.nf_crop_enqueue(5,300,600)==0
finally:assert d.nf_owned_gpu_close()==1
assert d.nf_crop_pending()==0
result=dict(result='PASS_COMPONENT',frames=checks,pack_state_preserved=True,queue_full_rejected=True,wrong_thread_rejected=True,pending_close_cleared=True,scope='Actual GL context solid-color target retention and API lifecycle; not full-scene/live integration or physical sky cadence proof.')
(p/'async-crop-component.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
