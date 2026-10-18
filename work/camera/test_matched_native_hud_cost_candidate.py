import ctypes as C,runpy,json,struct,statistics
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
original=extension.capture;count=0;trials=[]
library=C.CDLL(str(Path('work/camera/viewport-sky-bulk-hud-probe.dll').resolve()));bench=C.CDLL(str(Path('work/camera/hud-rows-cost-probe-candidate.dll').resolve()))
bench.nf_benchmark_hud.argtypes=[C.c_void_p,C.c_uint,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.c_uint,C.c_void_p];bench.nf_benchmark_hud.restype=C.c_int
size=160*34944;buffers=[C.create_string_buffer(size),C.create_string_buffer(size)]
functions=[library.nf_layer_queue_hud_row,library.nf_layer_queue_hud_rows_private]
def capture(address,epoch,refresh):
 global count
 packet=original(address,epoch,refresh);count+=1
 if count==40:
  geometry=struct.unpack_from('<I',packet,8)[0];expected=packet[40+geometry:40+geometry+size]
  for trial in range(8):
   row={}
   for kind in ((0,1) if trial%2==0 else (1,0)):
    timing=(C.c_uint64*3)();assert bench.nf_benchmark_hud(C.cast(functions[kind],C.c_void_p),kind,epoch,refresh,buffers[kind],size,10,timing)==1
    assert buffers[kind].raw[:size]==expected
    row['bulk' if kind else 'rowwise']=dict(ms=timing[0]*1000/timing[1]/10,cycles=timing[2]/10)
   trials.append(row)
 return packet
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_bulk_hud_candidate.py',run_name='__main__')
 assert len(trials)==8
 out=dict(result='PASS_MATCHED_NATIVE_HUD_ROWS_COST_PARITY',rows=trials,median_ms={k:statistics.median(x[k]['ms'] for x in trials) for k in ('rowwise','bulk')},median_cycles={k:statistics.median(x[k]['cycles'] for x in trials) for k in ('rowwise','bulk')},scope='Actual unchanged captured HUD source, alternating native10-read batches/identical private output. Warm-copy component cost only; cache residency and scheduling affected, not live frame gain or60fps proof.')
 Path('work/camera/prototype-runs/bulk-hud-matched-cost-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
finally:extension.capture=original
