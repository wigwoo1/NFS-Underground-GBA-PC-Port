import ctypes as C,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class Item(C.Structure):_fields_=[('older',U),('newer',U),('index',U),('deadline',U),('alpha',C.c_double),('drawctx',P),('presentctx',P)]
d=C.CDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()));d.nf_owned_batch_sample_size.restype=C.c_size_t;assert d.nf_owned_batch_sample_size()==C.sizeof(Item)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=d.nf_owned_handoff_batch;f.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P]
checks=[]
for mode in ['success','invalid_suffix','cancel_suffix']:
 q=d.nf_owned_handoff_create(7);calls=[]
 @CB
 def draw(ctx):
  calls.append(('draw',ctx))
  if mode=='cancel_suffix' and ctx==2:assert d.nf_owned_handoff_pause(q,1)
  return 0
 @CB
 def present(ctx):calls.append(('present',ctx));return 1
 items=(Item*3)(*[Item(10,14,20+i,0,(i+1)/4,i+1,i+1) for i in range(3)])
 if mode=='invalid_suffix':items[2].alpha=float('nan')
 samples=(U*24)(*([123]*24));waits=(U*12)();stages=(U*21)();completed=C.c_uint(99)
 try:
  result=f(q,7,1,items,3,draw,present,samples,waits,stages,C.byref(completed))
  if mode=='success':
   assert result==1 and completed.value==3 and calls==[('draw',1),('present',1),('draw',2),('present',2),('draw',3),('present',3)]
   assert [samples[i*8+4] for i in range(3)]==[20,21,22]
  elif mode=='invalid_suffix':assert result==-1 and completed.value==99 and not calls and list(samples)==[123]*24
  else:assert result==0 and completed.value==1 and calls==[('draw',1),('present',1),('draw',2)] and list(samples)[8:]==[123]*16
  checks.append(dict(mode=mode,result=result,completed=completed.value,calls=calls))
 finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-present-component-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Stand-in callback component; no native GPU batch/live input/pause publication proof.'),indent=2));print('PASS native batch identity, atomic metadata validation, retained canceled suffix')
