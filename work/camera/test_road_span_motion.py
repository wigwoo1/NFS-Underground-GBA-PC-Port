from pathlib import Path
import ctypes as C,json
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());short=0;motion=0
for height in [.0001,.01,.25,.75,.999999,1]:
 ring=[[0,0,0,50000,100000,200000],[10,height,0,60000,200000,300000],[20,0,0,70000,300000,400000]];data=(C.c_double*18)(*(v for row in ring for v in row))
 for ratio in [.0001,.25,.5,.75,.9999]:
  out=(C.c_double*8)();assert fn(data,3,height*ratio,table,out)
  expected=[10*ratio,100000+100000*ratio,200000+100000*ratio,50000+10000*ratio,20-10*ratio,300000-100000*ratio,400000-100000*ratio,70000-10000*ratio]
  assert max(abs(a-b) for a,b in zip(out,expected))<1e-8;short+=1
# Translating both source geometry and scan query must preserve attributes and shift X exactly.
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring']
 for row in [90.25,94.5,95.75,99.5,106.5,120.25]:
  original=(C.c_double*8)();data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));ok=fn(data,len(ring),row,table,original)
  if not ok:continue
  for shift in [-.75,-.25,.25,.75]:
   moved=[r.copy() for r in ring]
   for r in moved:r[0]+=shift;r[1]+=shift
   out=(C.c_double*8)();assert fn((C.c_double*(len(ring)*6))(*(v for r in moved for v in r)),len(ring),row+shift,table,out)
   expected=list(original);expected[0]+=shift;expected[4]+=shift;assert max(abs(a-b) for a,b in zip(out,expected))<1e-8;motion+=1
report=dict(result='PASS',short_edge_linear_checks=short,projected_translation_covariance_checks=motion,scope='Short-edge and projected translation component checks; world camera motion/GPU/fullscene timing unverified.');(p/'road-span-motion-tests.json').write_text(json.dumps(report,indent=2));print(report)
