import ctypes as C,json
from pathlib import Path
library=C.CDLL(str(Path('work/camera/owned-input-single-call-candidate.dll').resolve()));P=C.c_void_p
library.nf_input_poll_snapshot.argtypes=[P,P,P,C.c_size_t];library.nf_input_poll_snapshot_timed.argtypes=[P,P,P,P,C.c_size_t,P,C.c_size_t]
rows=[]
for fail in (None,'poll','stages','snapshot'):
 calls=[]
 @C.CFUNCTYPE(C.c_int,P)
 def poll(out):
  calls.append('poll');C.cast(out,C.POINTER(C.c_uint64))[0]=10;return 0 if fail=='poll' else 1
 @C.CFUNCTYPE(C.c_int,P)
 def stages(out):
  calls.append('stages')
  for i,v in enumerate((1,2,3,4)):C.cast(out,C.POINTER(C.c_uint64))[i]=v
  return 0 if fail=='stages' else 1
 @C.CFUNCTYPE(C.c_int,P)
 def snapshot(out):
  calls.append('snapshot')
  for i,v in enumerate((33,0,0,1)):C.cast(out,C.POINTER(C.c_uint32))[i]=v
  return 0 if fail=='snapshot' else 1
 timing=(C.c_uint64*5)();state=(C.c_uint32*4)();result=library.nf_input_poll_snapshot_timed(poll,stages,snapshot,timing,C.sizeof(timing),state,C.sizeof(state))
 expected={None:1,'poll':38,'stages':40,'snapshot':39}[fail];assert result==expected
 assert calls==({'poll':['poll'],'stages':['poll','stages']}.get(fail,['poll','stages','snapshot']))
 if fail is None:assert list(state)==[33,0,0,1] and list(timing)==[10,1,2,3,4]
 rows.append(dict(failure=fail,status=result,calls=calls))
@C.CFUNCTYPE(C.c_int)
def plain():calls.append('plain');return 1
calls=[];assert library.nf_input_poll_snapshot(plain,snapshot,state,C.sizeof(state))==39 and calls==['plain','snapshot']
calls=[];assert library.nf_input_poll_snapshot(None,snapshot,state,C.sizeof(state))==37 and calls==[]
assert library.nf_input_poll_snapshot(plain,snapshot,state,15)==37 and calls==[]
fail=None;calls=[]
assert library.nf_input_poll_snapshot(plain,snapshot,state,C.sizeof(state))==1 and calls==['plain','snapshot'] and list(state)==[33,0,0,1]
out=dict(result='PASS_INPUT_SINGLE_CALL_FORWARDING',cases=rows,scope='Native bridge callback order, bounds, null pointers, failure propagation and exact state/timing. Injected callbacks; no physical controller, focus behavior or live timing proof.')
Path('outputs/nfsug-native-renderer/camera-research/input-single-call-tests-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
