"""Xbox logical mapping through the actual queued renderer controller service."""
import ctypes as C,json,time
from pathlib import Path
class Pad(C.Structure):_fields_=[('buttons',C.c_uint16),('lt',C.c_uint8),('rt',C.c_uint8),('lx',C.c_int16),('ly',C.c_int16),('rx',C.c_int16),('ry',C.c_int16)]
class State(C.Structure):_fields_=[('packet',C.c_uint32),('pad',Pad)]
d=C.CDLL(str(Path('work/camera/owned-sky-queued-targets.dll').resolve()))
d.nf_controller_service_start.argtypes=[C.c_void_p];d.nf_controller_service_fresh_snapshot.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
CB=C.WINFUNCTYPE(C.c_uint32,C.c_uint32,C.POINTER(State));current={'slot':0,'pad':(0,0,0,0,0),'connected':True}
@CB
def callback(slot,target):
 if slot!=current['slot'] or not current['connected']:return 1167
 b,lt,rt,x,y=current['pad'];target.contents.pad=Pad(b,lt,rt,x,y,0,0);return 0
cases=[('neutral',(0,0,0,0,0),0),('A',(0x1000,0,0,0,0),1),('B',(0x2000,0,0,0,0),2),('back/start',(0x30,0,0,0,0),12),('dpad',(15,0,0,0,0),240),('shoulders',(0x300,0,0,0,0),768),('X/Y',(0xc000,0,0,0,0),768),('thresholds',(0,40,40,9000,-9000),0),('RT/right',(0,0,41,9001,0),17),('LT/left',(0,41,0,-9001,0),34),('up',(0,0,0,0,9001),64),('down',(0,0,0,0,-9001),128),('combined',(0xffff,255,255,32767,-32768),1023)]
out=(C.c_uint32*2)();serial=C.c_uint64();checks=[]
def await_sample(expected,after):
 deadline=time.monotonic()+3
 while time.monotonic()<deadline:
  assert d.nf_controller_service_fresh_snapshot(out,C.byref(serial),1000)
  if serial.value>after and list(out)==expected:return
  time.sleep(.001)
 raise AssertionError((expected,list(out),serial.value,after))
assert d.nf_controller_service_start(callback)
try:
 for slot in range(4):
  current['slot']=slot
  for name,pad,keys in cases:
   before=serial.value;current['pad']=pad;assert d.nf_controller_service_request();await_sample([keys,1],before)
   checks.append(dict(slot=slot,case=name,expected_game_keys=keys))
  before=serial.value;current['connected']=False;d.nf_controller_service_request();await_sample([0,0],before)
  before=serial.value;current['connected']=True;current['pad']=(0,0,0,0,0);d.nf_controller_service_request();await_sample([0,1],before)
finally:assert d.nf_controller_service_close(3000)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/queued-controller-mapping-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',mapping_cases=checks,disconnect_reconnect_slots=4,scope='Injected XInput states through actual queued renderer DLL polling worker/fresh snapshots; physical Xbox and game-response integration still unverified'),indent=2));print('PASS',len(checks),'mapping cases and4 disconnect/reconnect slots')
