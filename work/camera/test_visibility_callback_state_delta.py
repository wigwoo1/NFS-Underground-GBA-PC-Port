from pathlib import Path
import ctypes as C,json
root=Path('work/camera');fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_callback_state;fn.argtypes=[C.c_void_p]*9
passed=0
for lane in range(46):
 before=[list(range(32)),list(range(12)),[0,1]];after=[v.copy() for v in before];group=0 if lane<32 else 1 if lane<44 else 2;index=lane if group==0 else lane-32 if group==1 else lane-44
 after[group][index]+=1
 current=[[(v+7) for v in row] for row in before];current[group][index]=before[group][index]
 types=[C.c_uint8*32,C.c_uint32*12,C.c_uint32*2]
 original=[t(*v) for t,v in zip(types,before)];changed=[t(*v) for t,v in zip(types,after)]
 for stale in (False,True):
  actual=[t(*v) for t,v in zip(types,current)]
  if stale:actual[group][index]+=2
  old=[bytes(v) for v in actual];args=actual+[original[0],changed[0],original[1],changed[1],original[2],changed[2]]
  assert fn(*args)==int(not stale)
  if stale:assert [bytes(v) for v in actual]==old
  else:
   expected=[v.copy() for v in current];expected[group][index]=after[group][index]
   assert [list(v) for v in actual]==expected
  passed+=1
# Late stale global must prevent earlier bitmap and matrix writes.
b=(C.c_uint8*32)();m=(C.c_uint32*12)();g=(C.c_uint32*2)(0,9)
bb=(C.c_uint8*32)();ab=(C.c_uint8*32)(1);bm=(C.c_uint32*12)();am=(C.c_uint32*12)(1);bg=(C.c_uint32*2)();ag=(C.c_uint32*2)(0,1)
assert fn(b,m,g,bb,ab,bm,am,bg,ag)==0 and list(b)==[0]*32 and list(m)==[0]*12 and list(g)==[0,9]
report=dict(result='PASS',lane_success_and_stale_cases=passed,late_failure_atomic=True,scope='Callback state delta application, unchanged lanes preserve replay values; independent component tests.')
(root/'visibility-callback-state-delta-tests.json').write_text(json.dumps(report,indent=2));print(report)
