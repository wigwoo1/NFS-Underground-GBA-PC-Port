"""CPU-only HUD candidate profiling on actual owned scanlines; no render claim."""
import ctypes as C,json,struct,time,statistics,hashlib
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
d=C.CDLL(str(Path('work/camera/owned-sky-queued-targets.dll').resolve()));f=d.nf_obj_window_scanline_prepared;P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
f.argtypes=[P,Z,P,Z,P,Z,C.c_uint16,U,P,U,U,P,P,P,P];f.restype=C.c_int
vram=C.create_string_buffer(0x18000);colors=(C.c_uint32*240)();tags=(C.c_uint32*240)();controls=(C.c_uint8*240)();backdrop=(C.c_uint8*240)();checks=[]
for capture in r['wall_diagnostic_frames'][:3]:
 frame=Path(capture['regenerated']).read_bytes();h=struct.unpack_from('<6I2Q',frame);hud=frame[40+h[2]:40+h[2]+h[3]];assert len(hud)==160*34944
 rows=[]
 for y in range(160):
  row=hud[y*34944:(y+1)*34944];refresh,index=struct.unpack_from('<2I',row);assert refresh==h[1] and index==y
  regs=row[8:104];window=(C.c_uint16*6)(*struct.unpack_from('<6H',regs,64));rows.append((row,window,struct.unpack_from('<H',regs)[0],struct.unpack_from('<H',regs,80)[0],struct.unpack_from('<H',regs,84)[0]))
 trials=[];expected=None
 for trial in range(6):
  begin=time.perf_counter_ns();cpu=time.thread_time_ns();durations=[];signature=hashlib.sha256()
  for y,(row,window,display,blend,brightness) in enumerate(rows):
   C.memmove(C.addressof(vram)+0x10000,row[128:32896],32768)
   start=time.perf_counter_ns()
   assert f(vram,len(vram),row[32896:33920],1024,row[33920:34944],1024,display,y,window,blend,brightness,colors,tags,controls,backdrop)==1
   durations.append(time.perf_counter_ns()-start);signature.update(bytes(colors)+bytes(tags)+bytes(controls)+bytes(backdrop))
  signature=signature.hexdigest()
  if expected is None:expected=signature
  assert signature==expected
  trials.append(dict(wall_ms=(time.perf_counter_ns()-begin)/1e6,thread_cpu_ms=(time.thread_time_ns()-cpu)/1e6,max_native_row_ms=max(durations)/1e6,total_native_row_ms=sum(durations)/1e6))
 checks.append(dict(refresh=h[1],trials=trials,output_signature=expected))
out=dict(result='PASS_REPEATABLE_OWNED_HUD_CANDIDATES',checks=checks,scope='CPU-only actual captured160-row OBJ/window candidates; includes Python calling, copying and hashing. No GPU/upload/text/composition/presentation or complete fidelity proof.')
Path('work/camera/owned-hud-candidate-profile.json').write_text(json.dumps(out,indent=2));print([(x['refresh'],round(statistics.median(t['total_native_row_ms'] for t in x['trials']),3),round(max(t['max_native_row_ms'] for t in x['trials']),3)) for x in checks])
