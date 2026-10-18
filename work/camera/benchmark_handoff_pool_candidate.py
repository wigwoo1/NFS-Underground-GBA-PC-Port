import sys,json,ctypes as C,struct,time,statistics
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'captured_setup','exec'))
P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t
libraries={}
for name,file in [('original','owned-frame-handoff.dll'),('pool','owned-handoff-pool-candidate.dll')]:
 d=C.CDLL(str(Path('work/camera',file).resolve()))
 for function,args,result in [('create_capacity',[U,C.c_uint],P),('push_stages',[P,P,Z,P],C.c_int),('pop_token',[P,P,P],P),('destroy',[P],None)]:
  fn=getattr(d,'nf_owned_handoff_'+function);fn.argtypes=args;fn.restype=result
 d.nf_owned_frame_free.argtypes=[P];d.nf_owned_frame_free.restype=None
 d.nf_owned_frame_matches.argtypes=[P,Z,P,Z];d.nf_owned_frame_matches.restype=C.c_int
 libraries[name]=d
trials=[];epoch=struct.unpack_from('<Q',frames[0],24)[0]
for trial in range(12):
 for name in (['original','pool'] if trial%2==0 else ['pool','original']):
  d=libraries[name];q=d.nf_owned_handoff_create_capacity(epoch,2);copies=[];pushes=[];walls=[]
  try:
   for i in range(44):
    frame=frames[i%2];stages=(U*8)();begin=time.perf_counter_ns();assert d.nf_owned_handoff_push_stages(q,frame,len(frame),stages);end=time.perf_counter_ns()
    size=Z();generation=U();owner=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(generation));assert owner
    try:assert size.value==len(frame) and d.nf_owned_frame_matches(owner,size.value,frame,len(frame))
    finally:d.nf_owned_frame_free(owner)
    if i>=4:
     copies.append(stages[2]/stages[6]*1000);pushes.append(stages[5]/stages[6]*1000);walls.append((end-begin)/1e6)
   trials.append(dict(trial=trial,path=name,copy_allocation_median_ms=statistics.median(copies),native_push_median_ms=statistics.median(pushes),wrapper_median_ms=statistics.median(walls),samples=40))
  finally:d.nf_owned_handoff_destroy(q)
summary={name:{key:statistics.median([r[key] for r in trials if r['path']==name]) for key in ['copy_allocation_median_ms','native_push_median_ms','wrapper_median_ms']} for name in libraries}
out=dict(result='PASS_MATCHED_CAPTURED_HANDOFF_COST',summary=summary,trials=trials,scope='12 alternating paired serial component trials, two actual captured full frames, four warmups then40 samples per path. Every popped packet exact. Uncontrolled host; no live throughput or cadence proof.')
Path('work/camera/prototype-runs/handoff-pool-matched-cost-20261009.json').write_text(json.dumps(out,indent=2));print(summary)
