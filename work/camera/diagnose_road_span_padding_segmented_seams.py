from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));fn=dll.nf_road_span_padding_segmented;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=0;failures=[];physical=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 for shift in [0,.25,.5,.75]:
  ring=[[v+(shift if k==1 else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r))
  boundaries=sorted(set(list(range(161))+[r[1] for r in ring if 0<=r[1]<=160]))
  for row in boundaries:
   a=(C.c_double*2)();b=(C.c_double*2)();left=fn(data,len(ring),row-1e-8,table,a);right=fn(data,len(ring),row+1e-8,table,b)
   if not(left and right):continue
   checks+=1;gap=max(abs(x-y) for x,y in zip(a,b))
   if gap<1e-4:continue
   detail=dict(command=road['command'],shift=shift,row=row,gap=gap,left=list(a),right=list(b))
   horizontal=any(r[1]==ring[(i+1)%len(ring)][1]==row and r[0]!=ring[(i+1)%len(ring)][0] for i,r in enumerate(ring))
   (physical if horizontal else failures).append(detail)
report=dict(result='UNRESOLVED_NONPHYSICAL_SEAMS' if failures else 'PASS',two_sided_checks=checks,nonhorizontal_failures=failures,horizontal_boundaries=physical,scope='Segmented padding two-sided limit audit, source vertices and original integer row boundaries at four Y phases. Unresolved seams block continuous renderer adoption.');(p/'road-span-padding-segmented-seams.json').write_text(json.dumps(report,indent=2));print(dict(result=report['result'],checks=checks,nonhorizontal_failures=len(failures),horizontal_boundaries=len(physical),examples=failures[:3]))
