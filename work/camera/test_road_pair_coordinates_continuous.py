from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-coordinates-continuous.dll').resolve())).nf_road_pair_coordinates_continuous;fn.argtypes=[C.c_double,C.c_double,C.c_double,C.c_void_p]
def at(a,b,x):
 out=(C.c_double*3)(77,88,99);ok=fn(a,b,x,out);return ok,list(out)
integer=0
for left in range(-20,21):
 for gap in range(1,130):
  start=math.floor(left/2)*2;width=math.floor(gap/2)+2
  for relative in range(width*2):
   ok,out=at(left,left+gap,start+relative);assert ok and out==[start,width,relative//2];integer+=1
seams=0;maximum=0;eps=1e-8
for value in range(-20,21):
 for coordinate in range(3):
  # All queries interior; independently cross left, gap and query integer seams.
  args=[value, value+64, value+20]
  if coordinate==1:args=[0,value+64,20]
  if coordinate==2:args=[-40,100,value]
  a=args.copy();b=args.copy();a[coordinate]-=eps;b[coordinate]+=eps
  oa,va=at(*a);ob,vb=at(*b);assert oa and ob;gap=max(abs(x-y) for x,y in zip(va,vb));assert gap<1e-6;maximum=max(maximum,gap);seams+=1
for args in [(float('nan'),10,5),(0,0,0),(0,10,-1),(0,10,14)]:
 ok,out=at(*args);assert not ok and out==[77,88,99]
span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());actual_checks=actual_mismatches=0
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r))
 for row in range(161):
  edges=(C.c_double*8)()
  if not span(data,len(ring),row,table,edges):continue
  left,right=edges[0],edges[4];start=math.floor(left/2)*2;width=math.floor((right-left)/2)+2
  ok,value=at(left,right,start+4);actual_checks+=1
  if not ok or value!=[start,width,2]:actual_mismatches+=1
assert actual_mismatches>0
report=dict(result='REJECTED_FOR_ENDPOINT_ADOPTION',arithmetic_tests='PASS',actual_span_checks=actual_checks,actual_span_mismatches=actual_mismatches,integer_coordinate_checks=integer,seam_checks=seams,max_seam_gap=maximum,scope='Experimental continuous paired start/width/query coordinate extension preserves all tested integer anchors and interior seams. Does not establish original fractional-span fidelity, scan scheduling, visibility, clipping or fullscene smoothness.');(p/'road-pair-coordinates-continuous-tests.json').write_text(json.dumps(report,indent=2));print(report)
