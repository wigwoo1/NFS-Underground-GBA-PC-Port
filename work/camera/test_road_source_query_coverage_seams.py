from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-source-query-coverage.dll').resolve())).nf_road_source_query_coverage;fn.argtypes=[C.c_void_p,C.c_double,C.c_double,C.c_void_p];ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));writes=(C.c_int16*(38400*2))();assert ledger(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,writes)
 def sample(x,y):
  out=(C.c_double*3)();valid=fn(writes,x,y,out)
  return (out[0]*out[2],out[1]*out[2],out[2]) if valid else (0.,0.,0.)
 worst=[0.,0.,0.];count=0;failures=[]
 for axis in (0,1):
  for boundary in range(0,240 if axis==0 else 160):
   for other in range(160 if axis==0 else 240):
    a=(boundary-1e-8,other+.375) if axis==0 else (other+.375,boundary-1e-8)
    b=(boundary+1e-8,other+.375) if axis==0 else (other+.375,boundary+1e-8)
    left=sample(*a);right=sample(*b);gaps=[abs(x-y) for x,y in zip(left,right)];worst=[max(x,y) for x,y in zip(worst,gaps)];count+=1
    if max(gaps)>1e-5:failures.append(dict(axis=axis,boundary=boundary,other=other,gaps=gaps))
 assert not failures,(road['command'],failures[:5])
 checks.append(dict(command=road['command'],two_sided_cell_boundaries=count,max_premultiplied_row_x_coverage_gap=worst))
report=dict(result='PASS',checks=checks,scope='CPU weighted source-query coverage and premultiplied coordinates at all integer X/Y cells including viewport/empty boundaries. Static ledger query continuity only; does not prove geometry-motion or texture-index continuity.');(p/'road-source-query-coverage-seams.json').write_text(json.dumps(report,indent=2));print(report)
