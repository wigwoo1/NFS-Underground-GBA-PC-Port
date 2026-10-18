import ctypes as C,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class Item(C.Structure):_fields_=[('older',U),('newer',U),('index',U),('deadline',U),('alpha',C.c_double),('drawctx',P),('presentctx',P)]
d=C.CDLL(str(Path('work/camera/owned-batch-ready-reuse-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=d.nf_owned_handoff_batch_ready;f.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,CB,P]
checks=[]
for mode in ('ready','delayed','cancel_gate','error_gate','invalid_suffix'):
 q=d.nf_owned_handoff_create(7);calls=[];polls=[]
 @CB
 def draw(ctx):calls.append(('draw',ctx));return 0
 @CB
 def present(ctx):calls.append(('present',ctx));return 1
 @CB
 def ready(ctx):
  frame=calls[-1][1];polls.append(frame)
  if mode=='cancel_gate' and frame==2:d.nf_owned_handoff_pause(q,1);return 0
  if mode=='error_gate' and frame==2:return -1
  if mode=='delayed' and polls.count(frame)<3:return 0
  return 1
 items=(Item*3)(*[Item(10,14,20+i,0,.5,i+1,i+1) for i in range(3)])
 if mode=='invalid_suffix':items[2].alpha=float('nan')
 samples=(U*24)(*([123]*24));waits=(U*12)();stages=(U*21)();completed=C.c_uint(99)
 try:
  result=f(q,7,1,items,3,draw,present,samples,waits,stages,C.byref(completed),ready,None)
  if mode in ('ready','delayed'):
   assert result==1 and completed.value==3 and calls==[('draw',1),('present',1),('draw',2),('present',2),('draw',3),('present',3)]
   assert [samples[i*8+4] for i in range(3)]==[20,21,22]
   assert len(polls)==(9 if mode=='delayed' else 3)
  elif mode=='invalid_suffix':assert result==-1 and completed.value==99 and not calls and not polls
  else:assert result==(0 if mode=='cancel_gate' else -1) and completed.value==1 and calls==[('draw',1),('present',1),('draw',2)] and list(samples)[8:]==[123]*16
  handles=(U*4)();d.nf_owned_ready_handles.argtypes=[P]
  if mode!="invalid_suffix":
   assert d.nf_owned_ready_handles(handles)==1 and handles[0]==handles[1] and handles[0]<=1
  checks.append(dict(mode=mode,result=result,completed=completed.value,calls=calls,polls=polls))
 finally:d.nf_owned_handoff_destroy(q)
Path('work/camera/native-batch-ready-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Stand-in readiness callbacks; actual GPU gate and live integration still required'),indent=2));print('PASS readiness gate cancellation, error, validation, no double draw and retained suffix')
