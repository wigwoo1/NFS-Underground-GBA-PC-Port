import ctypes as C,time,json,shutil
from pathlib import Path
from owned_motion_clock import deadline
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class Item(C.Structure):_fields_=[('older',U),('newer',U),('index',U),('deadline',U),('alpha',C.c_double),('drawctx',P),('presentctx',P)]
d=C.CDLL(str(Path('work/camera/owned-batch-advance-candidate.dll').resolve()));d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_commit_sample.argtypes=[P,U,U,U,U,U,C.c_double,CB,P,P];d.nf_owned_handoff_last_sample.argtypes=[P,P]
f=d.nf_owned_handoff_batch_advance;f.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,U,P];checks=[]
for case in ('success','present_failure','pause_second_draw','future_skip','wrong_grid'):
 q=d.nf_owned_handoff_create(7);out=(U*16)();wait=(U*8)();stages=(U*14)();audits=(U*8)(*([777]*8));completed=C.c_uint(999);calls=[]
 @CB
 def initial(ctx):return 1
 @CB
 def draw(ctx):
  calls.append(['draw',ctx])
  if case=='pause_second_draw' and ctx==2:assert d.nf_owned_handoff_pause(q,1)==1
  return 0
 @CB
 def present(ctx):calls.append(['present',ctx]);return 0 if case=='present_failure' and ctx==2 else 1
 try:
  assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,10,.5,initial,None,out)==1
  origin=time.perf_counter_ns()-1000000000
  if case=='future_skip':origin=time.perf_counter_ns()+1000000000
  items=(Item*2)(*[Item(10,15,i,deadline(origin,i),.5,n,n) for n,i in enumerate((14,15),1)])
  if case=='wrong_grid':items[1].deadline+=1
  result=f(q,7,1,items,2,draw,present,out,wait,stages,C.byref(completed),origin,audits)
  expected={'success':1,'present_failure':-1,'pause_second_draw':0,'future_skip':-2,'wrong_grid':-1}[case];assert result==expected,(case,result)
  count={'success':2,'present_failure':1,'pause_second_draw':1,'future_skip':0,'wrong_grid':999}[case];assert completed.value==count
  last=(U*8)();assert d.nf_owned_handoff_last_sample(q,last)==1
  assert last[4]==(15 if case=='success' else 14 if case in ('present_failure','pause_second_draw') else 10)
  if count in (1,2):assert list(audits)[:2]==[10,3] and audits[3]>=audits[2]
  if count==2:assert list(audits)[4:]==[14,0,0,0]
  if case in ('future_skip','wrong_grid'):assert not calls and list(audits)==[777]*8
  checks.append(dict(case=case,result=result,completed=count,calls=calls,last_index=last[4],audits=list(audits)))
 finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/batch-advance-component-20261007');cp.mkdir(exist_ok=True)
for n in ('owned_batch_advance_candidate.c','owned_draw_advance_candidate.c','owned_presentation_advance_candidate.c','owned_frame_handoff.c','test_batch_advance_candidate.py'):shutil.copy2(Path('work/camera')/n,cp/n)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Separate synchronous batch DLL exact-grid advancement and successful-prefix publication; no live renderer or60fps verification.'),indent=2));print('PASS five batch advancement/prefix cases')
