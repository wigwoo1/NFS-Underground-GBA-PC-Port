import ctypes as C,struct,json,time,statistics,hashlib
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'obj-tile.dll').resolve()));f=d.nf_obj_window_scanline_prepared
f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint16,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
v=C.create_string_buffer(0x18000);colors=(C.c_uint32*240)();tags=(C.c_uint32*240)();controls=(C.c_uint8*240)();backdrop=(C.c_uint8*240)();results=[]
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 data=(p/f'motion-actual-scanline-assets/{refresh}-native-complete-frame.bin').read_bytes();gn=struct.unpack_from('<I',data,8)[0];rows=[]
 for y in range(160):
  raw=data[40+gn+y*34944:40+gn+(y+1)*34944];assert struct.unpack_from('<2I',raw)==(refresh,y)
  display=struct.unpack_from('<H',raw,8)[0];blend,alpha,brightness=struct.unpack_from('<3H',raw,88)
  rows.append((y,display,blend,brightness,C.create_string_buffer(raw[128:32896]),C.create_string_buffer(raw[32896:33920]),C.create_string_buffer(raw[33920:]),(C.c_uint16*6)(*struct.unpack_from('<6H',raw,72))))
 timings=[];digest=None
 for trial in range(4):
  h=hashlib.sha256();native_ns=copy_ns=0
  for y,display,blend,brightness,obj,palette,oam,window in rows:
   begin=time.perf_counter_ns();C.memmove(C.addressof(v)+0x10000,obj,0x8000);copied=time.perf_counter_ns()
   rc=f(v,len(v),palette,1024,oam,1024,display,y,window,blend,brightness,colors,tags,controls,backdrop);end=time.perf_counter_ns();assert rc==1,(refresh,y,rc)
   copy_ns+=copied-begin;native_ns+=end-copied
   h.update(bytes(colors));h.update(bytes(tags));h.update(bytes(controls));h.update(bytes(backdrop))
  current=h.hexdigest()
  if digest is not None:assert current==digest
  digest=current
  if trial:timings.append(dict(native_call_ms=native_ns/1e6,copy_ms=copy_ns/1e6))
 results.append(dict(refresh=refresh,rows=160,candidate_sha256=digest,samples=timings,median_native_call_ms=statistics.median(x['native_call_ms'] for x in timings)))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/captured-hud-native-cost-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='MEASURED_REPEAT_EXACT',results=results,scope='Actual seven captured HUD inputs, all160row candidate outputs deterministic across4runs. Native call includes ctypes overhead; excludes GPU composition/live scheduling, not original-core fidelity certification.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps([{k:v for k,v in x.items() if k!='samples'} for x in results]))
