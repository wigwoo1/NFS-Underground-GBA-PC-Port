import ctypes as C,time,threading,json
from pathlib import Path
p=Path(__file__).parent;d=C.CDLL(str((p/'owned-native-deadline-present-candidate.dll').resolve()));stub=C.CDLL(str((p/'native-present-bridge-test-stub.dll').resolve()))
P=C.c_void_p;U=C.c_uint64
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_epoch.argtypes=[P,U];d.nf_owned_handoff_close.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P]
f=d.nf_owned_native_deadline_present;f.argtypes=[P,U,U,U,U,U,C.c_double,U,P,P,P,P,P]
checks=[]
for action in ('pause','epoch','close'):
 q=d.nf_owned_handoff_create(1);stub.test_set(0);out=(U*8)(*[123]*8);wait=(U*4)();stages=(U*7)();status=C.c_int();answer=[];errors=[];started=threading.Event();deadline=time.perf_counter_ns()+500000000
 def waiter():
  try:
   started.set();answer.append(f(q,1,1,10,11,0,.5,deadline,C.cast(stub.test_present,P),out,wait,stages,C.byref(status)))
  except BaseException as error:errors.append(repr(error))
 thread=threading.Thread(target=waiter);thread.start()
 try:
  assert started.wait(2);time.sleep(.03);retired_at=time.perf_counter_ns()
  if action=='pause':assert d.nf_owned_handoff_pause(q,1)==1
  elif action=='epoch':assert d.nf_owned_handoff_epoch(q,2)==1
  else:d.nf_owned_handoff_close(q)
  thread.join(2);assert not thread.is_alive() and not errors
  assert answer==[0] and stub.test_calls()==0 and status.value==-999
  assert list(out)==[123]*8 and wait[0]<retired_at<wait[2]<deadline
  checks.append(dict(action=action,wait_begin_ns=wait[0],retire_begin_ns=retired_at,wait_end_ns=wait[2],deadline_ns=deadline,calls=stub.test_calls()))
 finally:
  if thread.is_alive():d.nf_owned_handoff_close(q);thread.join(2)
  assert not thread.is_alive();d.nf_owned_handoff_destroy(q)
result=dict(result='PASS_NATIVE_DEADLINE_WAIT_CANCELLATION',checks=checks,scope='Actual waiting native bridge canceled concurrently by pause, epoch and close; C presentation stub never invoked. Does not verify real graphics or live gameplay.')
(p/'prototype-runs/native-deadline-present-cancellation.json').write_text(json.dumps(result,indent=2));print(result['result'])
