import ctypes as C,json
from pathlib import Path
from owned_native_presentation_batch import BatchItem
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P);AC=C.CFUNCTYPE(C.c_int,C.POINTER(U));SC=C.CFUNCTYPE(C.c_int,U,U);RC=C.CFUNCTYPE(C.c_int,U)
h=C.CDLL(str(Path('work/camera/owned-batch-queued-candidate.dll').resolve()))
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P];h.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=h.nf_owned_handoff_batch_queued;f.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,AC,SC,RC,RC]
checks=[]
for case in ('ordered8','pause_before_first','pause_after_prefix','draw_failure','acquire_failure','ready_error','present_failure','invalid_suffix'):
 q=h.nf_owned_handoff_create(7);events=[];held={};state={'draw':0,'selected':0};done=C.c_uint(99);items=(BatchItem*8)()
 for i,x in enumerate(items):x.older=100;x.newer=104;x.index=i;x.deadline=0;x.alpha=.1+i*.1;x.drawctx=i+1;x.presentctx=i+1
 @CB
 def draw(ctx):
  state['draw']=ctx;events.append(['draw',ctx]);return 5 if case=='draw_failure' and ctx==3 else 0
 @AC
 def acquire(out):
  if case=='acquire_failure' and state['draw']==3:return 5
  token=state['draw'];out[0]=token;held[token]=token;events.append(['acquire',token]);return 0
 @SC
 def select(token,epoch):
  assert token in held and epoch==7;state['selected']=token;events.append(['select',token]);return 0
 @RC
 def release(token):
  assert token in held;del held[token];events.append(['release',token]);return 0
 @RC
 def ready(token):
  assert token in held
  if case=='pause_before_first' or case=='pause_after_prefix' and token==2:assert h.nf_owned_handoff_pause(q,1)==1
  return -1 if case=='ready_error' else 1
 @CB
 def present(ctx):
  assert state['selected']==ctx;events.append(['present',ctx]);return 0 if case=='present_failure' and ctx==2 else 1
 if case=='invalid_suffix':items[-1].alpha=2
 samples=(U*64)();waits=(U*32)();stages=(U*56)()
 try:
  result=f(q,7,1,items,8,draw,present,samples,waits,stages,C.byref(done),acquire,select,release,ready)
  assert not held,(case,held)
  if case=='ordered8':
   assert result==1 and done.value==8 and list(samples)[4::8]==list(range(8))
   assert [e[1] for e in events if e[0]=='present']==list(range(1,9));assert events.index(['draw',3])<events.index(['present',1])
  elif case=='invalid_suffix':assert result==-1 and not events and done.value==99
  elif case in ('pause_before_first','pause_after_prefix'):assert result==0 and done.value==(case=='pause_after_prefix')
  elif case=='present_failure':assert result==-1 and done.value==1
  else:assert result==-1 and done.value==0
  checks.append(dict(case=case,result=result,completed=done.value,events=events,leases_released=True))
 finally:h.nf_owned_handoff_destroy(q)
Path('work/camera/native-queued-batch-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print('PASS',len(checks),'ordered and cancellation cases')
