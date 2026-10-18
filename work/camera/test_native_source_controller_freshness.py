import ctypes as C,threading,time,json
from pathlib import Path
class Pad(C.Structure):
 _fields_=[('buttons',C.c_uint16),('lt',C.c_uint8),('rt',C.c_uint8),('lx',C.c_int16),('ly',C.c_int16),('rx',C.c_int16),('ry',C.c_int16)]
class State(C.Structure):_fields_=[('packet',C.c_uint32),('pad',Pad)]
d=C.CDLL(str(Path('work/camera/owned-gpu-source-context-free-candidate.dll').resolve()))
d.nf_controller_service_start.argtypes=[C.c_void_p];d.nf_controller_service_snapshot.argtypes=[C.c_void_p,C.c_void_p]
Callback=C.WINFUNCTYPE(C.c_uint32,C.c_uint32,C.POINTER(State));mode={'connected':True,'buttons':0x1000,'block':False};entered=threading.Event();release=threading.Event()
@Callback
def callback(i,out):
 if mode['block']:entered.set();release.wait(3)
 if i!=2 or not mode['connected']:return 1167
 out.contents.packet=1;out.contents.pad.buttons=mode['buttons'];return 0
checks=0
def check(x):
 global checks
 assert x;checks+=1
def snapshot():
 out=(C.c_uint32*2)();serial=C.c_uint64();assert d.nf_controller_service_snapshot(out,C.byref(serial));return list(out),serial.value
def await_state(expected):
 deadline=time.monotonic()+2
 while time.monotonic()<deadline:
  out,n=snapshot()
  if n and out==expected:return
  time.sleep(.002)
 raise AssertionError((out,n,expected))
check(not d.nf_controller_service_start(None));check(d.nf_controller_service_start(callback));check(not d.nf_controller_service_start(callback));await_state([1,1]);check(True)
mode['buttons']=0x2000;check(d.nf_controller_service_request());await_state([2,1]);check(True)
mode['connected']=False;d.nf_controller_service_request();await_state([0,0]);check(True)
mode['block']=True;d.nf_controller_service_request();check(entered.wait(2))
a=time.perf_counter();out,n=snapshot();elapsed=time.perf_counter()-a;check(elapsed<.05);check(not d.nf_controller_service_close(0));check(snapshot()[0]==[0,0]);release.set();check(d.nf_controller_service_close(3000));check(d.nf_controller_service_close(0));check(not d.nf_controller_service_request());check(not d.nf_controller_service_snapshot(None,None));mode['block']=False;mode['connected']=True;mode['buttons']=0x1000;check(d.nf_controller_service_start(callback));await_state([1,1]);check(d.nf_controller_service_close(3000))
# Hold accelerator then block device calls: age expiry clears it without waiting.
d.nf_controller_service_fresh_snapshot.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
mode['block']=False;mode['connected']=True;mode['buttons']=0x1000
check(d.nf_controller_service_start(callback));await_state([1,1])
out=(C.c_uint32*2)();serial=C.c_uint64()
check(d.nf_controller_service_fresh_snapshot(out,C.byref(serial),1000));check(list(out)==[1,1])
check(not d.nf_controller_service_fresh_snapshot(out,C.byref(serial),0));check(not d.nf_controller_service_fresh_snapshot(out,C.byref(serial),1001))
entered.clear();release.clear();mode['block']=True;d.nf_controller_service_request();check(entered.wait(2));time.sleep(.075)
check(d.nf_controller_service_fresh_snapshot(out,C.byref(serial),25));check(list(out)==[0,0])
# Release a delayed A response, and block the following read before it can publish.
release.set();deadline=time.monotonic()+2;old_serial=serial.value
while time.monotonic()<deadline:
 _,n=snapshot()
 if n>old_serial:break
 time.sleep(.001)
check(n>old_serial);check(d.nf_controller_service_fresh_snapshot(out,C.byref(serial),25))
# It may already have a genuinely new sample; expiry is checked again below.
release.clear();entered.clear();d.nf_controller_service_request();check(entered.wait(2));time.sleep(.075)
check(d.nf_controller_service_fresh_snapshot(out,C.byref(serial),25));check(list(out)==[0,0]);release.set();check(d.nf_controller_service_close(3000))
# Deterministically inspect a delayed connected response before any newer one.
first_entered=threading.Event();first_release=threading.Event();second_entered=threading.Event();second_release=threading.Event();calls=[0]
@Callback
def delayed_callback(i,target):
 calls[0]+=1
 if calls[0]==1:first_entered.set();first_release.wait(2)
 else:second_entered.set();second_release.wait(2)
 target.contents.pad.buttons=0x1000;return 0
check(d.nf_controller_service_start(delayed_callback));check(first_entered.wait(2));time.sleep(.075);first_release.set();d.nf_controller_service_request();check(second_entered.wait(2))
check(snapshot()[0]==[1,1]);check(d.nf_controller_service_fresh_snapshot(out,C.byref(serial),25));check(list(out)==[0,0]);second_release.set();check(d.nf_controller_service_close(3000))
result=dict(result='PASS',checks=checks,blocked_device_snapshot_ms=elapsed*1000,scope='Native worker component; mapped slot2, disconnect clears keys, blocked device does not block snapshot, timeout retains handles, clean retry/restart. Freshness clears held input and a deterministically delayed response cannot revive it. Live integration and physical Xbox pending.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-source-controller-20261008/freshness-tests.json').write_text(json.dumps(result,indent=2));print(result)
