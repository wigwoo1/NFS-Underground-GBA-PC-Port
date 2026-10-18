from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));span=dll.nf_road_span_transition_at;padfn=dll.nf_road_span_padding_segmented;span.argtypes=padfn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];pair=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;pair.argtypes=[C.c_double,C.c_double,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[];failures=[]
for fixture in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if fixture['ledger_accepted']:continue
 ring=fixture['rejected_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));covered=queries=0
 for y in range(2160):
  scan=(y+.5)/13.5;edges=(C.c_double*8)();padding=(C.c_double*2)(77,88);valid=span(data,len(ring),scan,table,edges);ok=padfn(data,len(ring),scan,table,padding)
  if bool(valid)!=bool(ok):failures.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],row=y,scan=scan,span=valid,padding=ok));continue
  if not ok:assert list(padding)==[77,88];continue
  covered+=1
  assert all(math.isfinite(v) for v in padding) and 1<=padding[1]<=32767
  for fraction in (.001,.25,.5,.75,.999):
   coordinate=C.c_double();assert pair(padding[1],2*padding[1]*fraction,C.byref(coordinate));sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),padding[1],coordinate.value,table,sample);assert all(math.isfinite(v) for v in sample);queries+=1
 checks.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],native_rows=2160,covered_rows=covered,uv_queries=queries))
report=dict(result='PASS' if not failures else 'FAIL',checks=checks,failures=failures,scope='CPU direct continuous span/padding/pair/UV at native4K rows for world-derived fractional geometry rejected by integer endpoint ledger. Does not solve original winner scheduling, final boundary coverage, GPU or full-scene motion.');(p/'world-fractional-road-native-sampler-tests.json').write_text(json.dumps(report,indent=2));print(report);assert not failures
