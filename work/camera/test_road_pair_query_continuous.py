from pathlib import Path
import ctypes as C,json,sys,math
p=Path('work/camera');query=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;query.argtypes=[C.c_double,C.c_double,C.c_void_p];continuous=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];lane_checks=0
s=(p/'test_native_road_pair_uv.py').read_text();s=s.replace('tested+=1',"""tested+=1
  for lane in range(2):
   coordinate=C.c_double(-77);assert query(width,pair*2+lane,C.byref(coordinate));assert coordinate.value==pair
   composed=(C.c_double*2)();assert continuous((C.c_double*3)(*a[1:]),(C.c_double*3)(*b[1:]),width,coordinate.value,table,composed);assert list(composed)==fixed;lane_checks+=1""".replace(chr(10),chr(92)+"n"))
exec(compile(s,'composed_query_integer_endpoint','exec'),globals())
seams=0;maximum=0
for width in [1,1.25,2,2.75,32,32.25,64,64.75]:
 for relative in range(1,int(2*width)):
  a=C.c_double();b=C.c_double();assert query(width,relative-1e-8,C.byref(a)) and query(width,relative+1e-8,C.byref(b));gap=abs(a.value-b.value);assert gap<1e-6;maximum=max(maximum,gap);seams+=1
 out=C.c_double();assert query(width,math.nextafter(2*width,0),C.byref(out));assert 0<=out.value<=width-1
for width,relative in [(float('nan'),0),(1,float('nan')),(0,0),(32768,0),(10,-1),(10,20)]:
 out=C.c_double(77);assert not query(width,relative,C.byref(out)) and out.value==77
report=dict(result='PASS',exact_original_lane_uv_compositions=lane_checks,pair_queries=tested,two_sided_coordinate_seams=seams,max_gap=maximum,scope='Candidate horizontal pair query preserves original lane UV and continuous interior/terminal pair coordinates; texture lane address, doubled rows, finalGPU native coverage and motion remain pending.');(p/'road-pair-query-continuous-tests.json').write_text(json.dumps(report,indent=2));print(report)
