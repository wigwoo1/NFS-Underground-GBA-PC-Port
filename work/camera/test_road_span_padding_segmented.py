from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));fn=dll.nf_road_span_padding_segmented;span=dll.nf_road_span_transition_at;fn.argtypes=span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 for shift in [0,.25,.5,.75]:
  ring=[[v+(shift if k==1 else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));covered=integer=0
  for i in range(2160):
   row=(i+.5)/13.5;edges=(C.c_double*8)();valid=span(data,len(ring),row,table,edges);out=(C.c_double*2)(77,88);ok=fn(data,len(ring),row,table,out);assert bool(ok)==bool(valid),(road['command'],shift,row,valid,ok)
   if ok:assert all(math.isfinite(v) for v in out) and out[1]>=1;covered+=1
   else:assert list(out)==[77,88]
  for row in range(161):
   edges=(C.c_double*8)();valid=span(data,len(ring),row,table,edges);out=(C.c_double*2)();ok=fn(data,len(ring),row,table,out);assert bool(ok)==bool(valid)
   if ok:assert list(out)==[2*math.floor(edges[0]/2),math.floor((edges[4]-edges[0])/2)+2];integer+=1
  checks.append(dict(command=road['command'],shift=shift,native_row_queries=2160,covered_rows=covered,exact_integer_padding=integer))
report=dict(result='PASS',checks=checks,scope='Segmented fractional padding component, source-span coverage status preserved at all native4K queryrows for four Y phases. No complete UV/index/nativecoverage/worldmotion proof.');(p/'road-span-padding-segmented-tests.json').write_text(json.dumps(report,indent=2));print(report)
