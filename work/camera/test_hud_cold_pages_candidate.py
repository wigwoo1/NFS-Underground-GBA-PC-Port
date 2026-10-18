import ctypes as C,runpy,json,struct,statistics
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
original=extension.capture;count=0;trials=[]
library=C.CDLL(str(Path('work/camera/viewport-sky-bulk-direct-pages-probe.dll').resolve()))
bench=C.CDLL(str(Path('work/camera/hud-cold-pages-candidate.dll').resolve()))
bench.nf_cold_hud.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p];bench.nf_cold_hud.restype=C.c_int
size=160*34944;output=C.create_string_buffer(size)
def capture(address,epoch,refresh):
 global count
 packet=original(address,epoch,refresh);count+=1
 if count==40:
  geometry=struct.unpack_from('<I',packet,8)[0];expected=packet[40+geometry:40+geometry+size]
  for trial in range(12):
   timing=(C.c_uint64*5)()
   assert bench.nf_cold_hud(C.cast(library.nf_layer_queue_hud_rows_private,C.c_void_p),epoch,refresh,output,size,timing)==1
   assert output.raw[:size]==expected
   trials.append(dict(cold_ms=timing[0]*1000/timing[4],cold_cycles=timing[1],warm_ms=timing[2]*1000/timing[4],warm_cycles=timing[3]))
 return packet
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_bulk_direct_pages_candidate.py',run_name='__main__')
 assert len(trials)==12
 result=dict(result='PASS_COLD_WARM_NATIVE_HUD_PARITY',trials=trials,medians={k:statistics.median(t[k] for t in trials) for k in trials[0]},scope='Fresh committed VirtualAlloc pages versus immediate second write to same pages, same actual immutable HUD source. Includes first-touch faults; excludes allocation cost. Fixed cold-first order and intervening parity copy perturb caches. Not actual PyBytes residency or live60fps proof.')
 Path('work/camera/prototype-runs/hud-cold-pages-20261009.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['medians']))
finally:extension.capture=original
