from pathlib import Path
import ctypes as C,json,random,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-source-query-continuous.dll').resolve())).nf_road_source_query_continuous;fn.argtypes=[C.c_void_p,C.c_double,C.c_double,C.c_void_p];ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());rng=random.Random(20251005);checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));bounds=(C.c_uint16*4)(*road['bounds']);writes=(C.c_int16*(38400*2))();assert ledger(data,len(ring),bounds,table,writes);integer=covered=fractional=rejected=seams=0;maximum=0
 for y in range(160):
  for x in range(240):
   at=y*240+x;out=(C.c_double*2)(77,88);ok=fn(writes,x,y,out);assert bool(ok)==(writes[at*2]>=0);integer+=1
   if ok:assert list(out)==list(writes[at*2:at*2+2]);covered+=1
   else:assert list(out)==[77,88]
 for _ in range(10000):
  x=rng.randrange(239)+rng.randrange(1,16)/16;y=rng.randrange(159)+rng.randrange(1,16)/16;ix=int(x);iy=int(y);corners=[writes[((iy+dy)*240+ix+dx)*2:((iy+dy)*240+ix+dx)*2+2] for dy in range(2) for dx in range(2)];out=(C.c_double*2)(77,88);ok=fn(writes,x,y,out);valid=all(v[0]>=0 for v in corners);assert bool(ok)==valid
  if ok:
   weights=[(1-(x-ix))*(1-(y-iy)),(x-ix)*(1-(y-iy)),(1-(x-ix))*(y-iy),(x-ix)*(y-iy)];want=[sum(w*v[k] for w,v in zip(weights,corners)) for k in range(2)];assert list(out)==want;fractional+=1
  else:assert list(out)==[77,88];rejected+=1
 for y in range(1,159):
  for x in range(1,239):
   a=(C.c_double*2)();b=(C.c_double*2)();left=fn(writes,x-1e-8,y+.25,a);right=fn(writes,x+1e-8,y+.25,b)
   if left and right:gap=max(abs(i-j) for i,j in zip(a,b));assert gap<1e-4;maximum=max(maximum,gap);seams+=1
 checks.append(dict(command=road['command'],integer_queries=integer,covered_integer=covered,fractional_queries=fractional,visibility_rejections=rejected,two_sided_interior_seams=seams,max_gap=maximum))
report=dict(result='PASS',checks=checks,scope='Native geometry write-ledger query interpolation only: exact original winners, covered-cell interior continuity. Fractional visibility boundaries deliberately reject, not adopted as final coverage; no world motion/GPU proof.');(p/'road-source-query-continuous-tests.json').write_text(json.dumps(report,indent=2));print(report)
