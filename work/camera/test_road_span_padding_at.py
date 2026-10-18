from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-at.dll').resolve()));fn=dll.nf_road_span_padding_at;span=dll.nf_road_span_transition_at;fn.argtypes=span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());integer=seams=fractional=boundary_rejections=0;maximum=0;failures=[];physical_boundaries=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r))
 def evaluate(row):
  out=(C.c_double*2)(77,88);ok=fn(data,len(ring),row,table,out);return ok,list(out)
 for row in range(161):
  edges=(C.c_double*8)();valid=span(data,len(ring),row,table,edges);ok,out=evaluate(row);assert bool(ok)==bool(valid)
  if valid:
   want=[2*math.floor(edges[0]/2),math.floor((edges[4]-edges[0])/2)+2];assert out==want;integer+=1
   a,x=evaluate(row-1e-8);b,y=evaluate(row+1e-8)
   if a and b:
    gap=max(abs(i-j) for i,j in zip(x,y));maximum=max(maximum,gap);seams+=1
    if gap>=1e-4:
     horizontal=any(r[1]==ring[(i+1)%len(ring)][1]==row and r[0]!=ring[(i+1)%len(ring)][0] for i,r in enumerate(ring))
     detail=dict(command=road['command'],row=row,gap=gap,left=x,right=y)
     if horizontal:
      before=(C.c_double*8)();assert span(data,len(ring),math.nextafter(row,row-1),table,before)
      assert abs(x[0]-2*math.floor(before[0]/2))<1e-4
      assert abs(x[1]-(math.floor((before[4]-before[0])/2)+2))<1e-4
      physical_boundaries.append(detail)
     else:failures.append(detail)
  else:assert out==[77,88]
  if row<160:
   for t in [.25,.5,.75]:
    ok,out=evaluate(row+t)
    if ok:assert all(math.isfinite(v) for v in out);fractional+=1
    else:assert out==[77,88];boundary_rejections+=1
shifted=[[v+(.25 if k==1 else 0) for k,v in enumerate(r)] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks'][0]['clipped_ring']]
shifted_data=(C.c_double*(len(shifted)*6))(*(v for r in shifted for v in r));sentinel=(C.c_double*2)(77,88);assert not fn(shifted_data,len(shifted),91.5,table,sentinel) and list(sentinel)==[77,88]
assert not failures
report=dict(result='INCOMPLETE_TOPOLOGY_SEAMS' if failures else 'PASS',seam_failures=failures,verified_one_sided_horizontal_boundaries=physical_boundaries,exact_original_span_padding=integer,two_sided_seams=seams,max_gap=maximum,fractional_queries=fractional,atomic_empty_or_topology_rejections=boundary_rejections,scope='Source-span anchored row padding component. Fractional rows require two valid boundary spans; subcell horizontal topology explicitly rejects atomically; moving snapshot phase, paired query coordinate and fullGPU coverage remain unresolved.');(p/'road-span-padding-at-tests.json').write_text(json.dumps(report,indent=2));print(report)
