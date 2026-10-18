import ctypes as C,time,json,shutil
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-draw-advance-candidate.dll').resolve()));d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
d.nf_owned_handoff_commit_sample.argtypes=[P,U,U,U,U,U,C.c_double,CB,P,P]
f=d.nf_owned_handoff_draw_wait_advance_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,U,CB,P,CB,P,P,P,P,P]
checks=[]
for case in ('future','overflow','wrong_previous','draw_failure','pause_during_draw','due_wait'):
 q=d.nf_owned_handoff_create(7);out=(U*8)();wait=(U*4)();stages=(U*7)();audit=(U*4)(777,888,999,111);calls=[]
 @CB
 def present(ctx):calls.append('present');return 1
 @CB
 def draw(ctx):
  calls.append('draw')
  if case=='pause_during_draw':assert d.nf_owned_handoff_pause(q,1)==1
  return -1 if case=='draw_failure' else 0
 try:
  assert d.nf_owned_handoff_commit_sample(q,7,1,10,15,10,.5,present,None,out)==1;calls.clear();before=list(out)
  origin=time.perf_counter_ns()-233333334+5000000
  if case=='future':origin=time.perf_counter_ns()+1000000000
  if case=='overflow':origin=2**64-1
  previous=9 if case=='wrong_previous' else 10
  result=f(q,7,1,10,15,14,.5,origin,previous,draw,None,present,None,out,wait,stages,audit)
  expected={'future':-2,'overflow':-1,'wrong_previous':-1,'draw_failure':-1,'pause_during_draw':0,'due_wait':1}[case];assert result==expected,(case,result)
  if case=='due_wait':
   assert calls==['draw','present'] and out[4]==14 and out[7]==2
   assert out[6]>=origin+233333334 and list(audit)[:2]==[10,3]
   assert audit[2]==origin+216666667 and audit[3]>=audit[2]
  else:
   assert list(out)==before and list(audit)==[777,888,999,111]
   assert calls==(['draw'] if case in ('draw_failure','pause_during_draw') else [])
  checks.append(dict(case=case,result=result,calls=calls,audit=list(audit)))
 finally:d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/draw-advance-deadlines-20261007');cp.mkdir(exist_ok=True)
for name in ('owned_draw_advance_candidate.c','owned_presentation_advance_candidate.c','owned_frame_handoff.c','test_draw_advance_candidate.py'):shutil.copy2(Path('work/camera')/name,cp/name)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Native exact60Hz deadline eligibility, future/overflow/stale previous rejects, failed draw and pause revalidation, no early successful commit. Isolated component; not live60fps or original game verification.'),indent=2));print('PASS six draw/advance deadline cases')
