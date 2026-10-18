from pathlib import Path
import ctypes as C,json
from road_scheduled_coverage import scheduled_spans,coverage_buffer
p=Path('work/camera');intervals=json.loads((p/'road-actual-temporal-domain-tests.json').read_text())['checks'];bounds={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];checks=[];endpoint_pixels=0;interior_pixels=0
for interval in intervals:
 poses=interval['phases'];a,b=poses[0]['ring'],poses[-1]['ring'];bd=bounds[interval['command']];samples=[]
 for pose in poses:
  phase=pose['phase'];current=pose['ring'];spans=scheduled_spans(a,b,current,bd,table,phase);buffer=coverage_buffer(spans);assert all(0<=sum(v[3] for v in items)<=1+1e-12 for items in buffer)
  if phase in (0.,1.):
   data=(C.c_double*(len(current)*6))(*(v for r in current for v in r));writes=(C.c_int16*(38400*2))();assert ledger(data,len(current),(C.c_uint16*4)(*bd),table,writes)
   for d,items in enumerate(buffer):
    row,x=writes[d*2:d*2+2];expected=[] if row<0 else [(float(row),float(x),1.)];assert [(v[1],v[2],v[3]) for v in items]==expected,(interval['command'],interval['begin_a'],phase,d,items,expected);endpoint_pixels+=1
  else:interior_pixels+=38400
  samples.append(dict(phase=phase,spans=len(spans),covered_destinations=sum(bool(v) for v in buffer),partial_destinations=sum(0<sum(v[3] for v in items)<1 for items in buffer),maximum_contributors=max(map(len,buffer))))
 checks.append(dict(command=interval['command'],begin_a=interval['begin_a'],samples=samples));print(interval['command'],interval['begin_a'],'PASS',flush=True)
report=dict(result='PASS_ORDERED_COVERAGE_COMPONENT',exact_endpoint_pixels=endpoint_pixels,bounded_interior_pixels=interior_pixels,checks=checks,scope='Actual18poseinterval ordered schedule/horizontal-span/vertical-lifetime/duplicate/spill coverage at240x160. Exact36endpoint sourcewinnerbuffers;54interiorcoveragebuffers bounded. No motion-continuity/material correspondence/UV/color/GPU/fullscene/native4K/live timing proof.')
(p/'road-scheduled-coverage-tests.json').write_text(json.dumps(report,indent=2));print(report['result'],endpoint_pixels,interior_pixels)
