import ctypes as C,json,runpy,sys
from pathlib import Path
kernel=C.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=C.c_void_p;kernel.GetProcessHandleCount.argtypes=[C.c_void_p,C.c_void_p]
def handles():
 n=C.c_uint();assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(),C.byref(n));return n.value
source=Path('work/camera/test_handoff_precise_candidate.py').read_text();results=[]
for dll in ['owned-frame-handoff-precise-candidate.dll','owned-frame-handoff-create-failure-test.dll','owned-frame-handoff-set-failure-test.dll']:
 test=source.replace('owned-frame-handoff-precise-candidate.dll',dll);ns={};exec(compile(test,'timer_guard_test','exec'),ns)
 before=handles()
 for i in range(100):
  d=ns['d'];q=d.nf_owned_handoff_create(1);v=(C.c_uint64*4)()
  try:
   deadline=ns['time'].perf_counter_ns()+1000000;assert d.nf_owned_handoff_wait_token(q,1,1,deadline,v)==1 and v[2]>=deadline
  finally:d.nf_owned_handoff_destroy(q)
 after=handles();assert after==before,(dll,before,after)
 results.append(dict(dll=dll,deadline_and_retirement=ns['out'],repeat_waits=100,handles_before=before,handles_after=after))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/handoff-precise-20261008');(cp/'resources-fallback.json').write_text(json.dumps(dict(result='PASS',cases=results,scope='Separate compile-time creation and arm failure variants exercise unchanged fallback. Process handle count measured after warmup in isolated test; no live pacing claim.'),indent=2));print('PASS all 3 variants, 300 repeat waits, zero retained handles')
