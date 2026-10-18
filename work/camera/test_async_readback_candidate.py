import ctypes as C,hashlib,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-async-readback-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64
for name,args in [('nf_d3d_clear',[P]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_async_capture',[C.c_uint,U]),('nf_d3d_async_poll',[C.c_uint,U,P,C.c_size_t]),('nf_d3d_async_stats',[P])]:getattr(d,name).argtypes=args
assert d.nf_d3d_open()==0;buf=C.create_string_buffer(3840*2160*4);references=[];checks=[]
try:
 for slot,color in enumerate(((1,0,0,1),(0,1,0,1),(0,0,1,1))):
  assert d.nf_d3d_clear((C.c_float*4)(*color))==0;assert d.nf_d3d_async_capture(slot,100+slot)==0
  assert d.nf_d3d_read(buf,len(buf))==0;references.append(hashlib.sha256(buf.raw).hexdigest())
 assert d.nf_d3d_async_capture(0,999)==1
 assert d.nf_d3d_async_poll(0,999,buf,len(buf))==1 and d.nf_d3d_async_poll(0,100,buf,len(buf)-1)==1
 errors=[];t=threading.Thread(target=lambda:errors.append(d.nf_d3d_async_poll(0,100,buf,len(buf))));t.start();t.join();assert errors==[1]
 for slot in range(3):
  assert d.nf_d3d_async_poll(slot,100+slot,buf,len(buf))==0
  actual=hashlib.sha256(buf.raw).hexdigest();assert actual==references[slot];checks.append(dict(slot=slot,sha256=actual))
 assert d.nf_d3d_async_poll(0,100,buf,len(buf))==1
 assert d.nf_d3d_async_capture(0,200)==0
finally:assert d.nf_d3d_close()==0
stats=(C.c_uint*2)();assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[0,0]
out=dict(result='PASS_ASYNC_READBACK_IDENTITIES_PARITY_GUARDS',snapshots=checks,occupied_slot_not_overwritten=True,wrong_identity_and_size_rejected=True,wrong_owner_rejected=True,consumed_slot_rejected=True,pending_resources_released=True,scope='Three actual4K queued snapshots match synchronous targets despite later target changes. Synchronous reference reads flush GPU in this component; does not measure nonblocking live cadence or pending return behavior.')
(p/'prototype-runs/async-readback-component-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
