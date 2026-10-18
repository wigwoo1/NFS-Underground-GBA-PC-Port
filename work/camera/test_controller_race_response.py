"""Injected Xbox service input versus expected controls in original race simulation."""
import ctypes as C,json,time,hashlib,runpy
from pathlib import Path
scope={};exec(Path('work/camera/test_queued_controller_mapping.py').read_text().split('out=(C.c_uint32*2)')[0],scope)
d=scope['d'];current=scope['current'];callback=scope['callback']
out=(C.c_uint32*2)();serial=C.c_uint64()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/controller-race-response-20261007');cp.mkdir(exist_ok=True)
g=C.CDLL(str(Path('work/nfsprobe.dll').resolve()));g.nf_init.argtypes=[C.c_char_p,C.c_char_p];g.nf_state.argtypes=[C.c_char_p,C.c_int];g.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=Path('work/race.state').resolve()
segments=[('accelerate',(0,0,255,0,0),1),('right',(0,0,255,20000,0),17),('left',(0,0,255,-20000,0),33),('brake',(0,255,0,0,0),2),('neutral',(0,0,0,0,0),0)]
streams={'controller':[],'expected':[],'neutral':[0]*300}
assert d.nf_controller_service_start(callback)
try:
 for name,pad,expected in segments:
  current['pad']=pad;before=serial.value;assert d.nf_controller_service_request()
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   assert d.nf_controller_service_fresh_snapshot(out,C.byref(serial),1000)
   if serial.value>before and out[0]==expected and out[1]==1:break
  else:raise AssertionError(name)
  streams['controller'].extend([out[0]]*60);streams['expected'].extend([expected]*60)
finally:assert d.nf_controller_service_close(3000)
results={}
for label,keys in streams.items():
 assert g.nf_init(str(rom).encode(),b'') and g.nf_state(str(state).encode(),0)
 try:
  for key in keys:g.nf_frame(key)
  results[label]={}
  for region,address,size in [('ewram',0x02000000,262144),('iwram',0x03000000,32768)]:
   path=(cp/(label+'-'+region+'.bin')).resolve();g.nf_dump(str(path).encode(),address,size);data=path.read_bytes();assert len(data)==size;results[label][region]=data
 finally:g.nf_close()
assert results['controller']==results['expected']
assert results['controller']!=results['neutral'],'Input did not change original simulation state'
result=dict(result='PASS_INJECTED_CONTROLLER_RACE_RESPONSE',updates_per_stream=300,segments=[dict(name=n,keys=k,updates=60) for n,p,k in segments],hashes={k:{r:hashlib.sha256(b).hexdigest() for r,b in v.items()} for k,v in results.items()},scope='Actual queued renderer controller service with injected Xbox states mapped into actual original race core. Final full RAM equals expected direct controls and differs from neutral. No physical controller/window focus/visual driving proof.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result,indent=2))
