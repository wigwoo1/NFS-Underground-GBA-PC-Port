import ctypes as C,hashlib,json,threading,numpy as np
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-textured-sky-roi-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64
for name,args in [('nf_d3d_clear',[P]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_async_capture',[C.c_uint,U]),('nf_d3d_async_poll',[C.c_uint,U,P,C.c_size_t]),('nf_d3d_async_stats',[P])]:getattr(d,name).argtypes=args
assert d.nf_d3d_open()==0;buf=C.create_string_buffer(3840*2160*4);roi=C.create_string_buffer(512*64*4);references=[];checks=[]
try:
 for slot,color in enumerate(((1,0,0,1),(0,1,0,1),(0,0,1,1))):
  assert d.nf_d3d_clear((C.c_float*4)(*color))==0;rows=np.zeros((160,4),np.uint8);rows[:,0]=np.arange(160);rows[:,1]=slot*80;rows[:,2]=255-np.arange(160);rows[:,3]=255;d.nf_d3d_backdrop_rows.argtypes=[P,C.c_size_t];assert d.nf_d3d_backdrop_rows(rows.ctypes.data,640)==0;assert d.nf_d3d_async_capture(slot,100+slot)==0
  assert d.nf_d3d_read(buf,len(buf))==0;import numpy as np;crop=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)[918:982,300:812].tobytes();references.append(hashlib.sha256(crop).hexdigest())
 assert d.nf_d3d_async_capture(0,999)==1
 assert d.nf_d3d_async_poll(0,999,roi,len(roi))==1 and d.nf_d3d_async_poll(0,100,roi,len(roi)-1)==1
 errors=[];t=threading.Thread(target=lambda:errors.append(d.nf_d3d_async_poll(0,100,roi,len(roi))));t.start();t.join();assert errors==[1]
 for slot in range(3):
  assert d.nf_d3d_async_poll(slot,100+slot,roi,len(roi))==0
  actual=hashlib.sha256(roi.raw).hexdigest();assert actual==references[slot];checks.append(dict(slot=slot,sha256=actual))
 assert d.nf_d3d_async_poll(0,100,roi,len(roi))==1
 assert d.nf_d3d_async_capture(0,200)==0
finally:assert d.nf_d3d_close()==0
stats=(C.c_uint*2)();assert d.nf_d3d_async_stats(stats)==0 and list(stats)==[0,0]
out=dict(result='PASS_ASYNC_READBACK_IDENTITIES_PARITY_GUARDS',snapshots=checks,occupied_slot_not_overwritten=True,wrong_identity_and_size_rejected=True,wrong_owner_rejected=True,consumed_slot_rejected=True,pending_resources_released=True,scope='Three row-gradient target snapshots at region300,918,512,64 match synchronous4K crops despite later target changes. Synchronous reference reads flush GPU; no live cadence claim.')
(p/'prototype-runs/textured-roi-component-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
