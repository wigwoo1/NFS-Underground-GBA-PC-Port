from pathlib import Path
import ctypes as C,json,sys,random
p=Path('work/camera');continuous=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];tested=0
s=(p/'test_native_road_pair_uv.py').read_text();s=s.replace('tested+=1',"tested+=1;fractional_out=(C.c_double*2)();assert continuous((C.c_double*3)(*a[1:]),(C.c_double*3)(*b[1:]),width,pair,table,fractional_out);assert list(fractional_out)==fixed")
exec(compile(s,'continuous_endpoint_differential','exec'),globals())
def evaluate(v):
 out=(C.c_double*2)(77,88);ok=continuous((C.c_double*3)(*v[:3]),(C.c_double*3)(*v[3:6]),v[6],v[7],table,out);assert ok;return list(out)
base=[100000,200000,60000,150000,250000,50000,64,20];epsilon=1e-8;checks=0;maximum=0
for coordinate in range(8):
 for seam in ([32,33,64] if coordinate==6 else [15,16,31,32] if coordinate==7 else [base[coordinate]-1,base[coordinate],base[coordinate]+1]):
  a=base.copy();b=base.copy();a[coordinate]=seam-epsilon;b[coordinate]=seam+epsilon
  x=evaluate(a);y=evaluate(b);gap=max(abs(i-j) for i,j in zip(x,y));assert gap<.05,(coordinate,seam,gap);maximum=max(maximum,gap);checks+=1
bad=(C.c_double*2)(77,88);assert not continuous((C.c_double*3)(float('nan'),0,1),(C.c_double*3)(0,0,1),64,20,table,bad);assert list(bad)==[77,88]
final_checks=0
for width in [1.25,1.75,2.25,2.75,31.25,31.75,32.25,32.75,63.25,63.75]:
 v=base.copy();v[6]=width;v[7]=width-1;endpoint=evaluate(v);v[7]-=epsilon;inside=evaluate(v);assert max(abs(a-b) for a,b in zip(endpoint,inside))<.05;final_checks+=1
for seam in [2,32,33,64]:
 a=base.copy();b=base.copy();a[6]=seam-epsilon;b[6]=seam+epsilon;a[7]=a[6]-1;b[7]=b[6]-1
 assert max(abs(x-y) for x,y in zip(evaluate(a),evaluate(b)))<.05;final_checks+=1
report=dict(result='PASS',exact_integer_endpoint_checks=tested,final_pair_boundary_checks=final_checks,two_sided_cell_seams=checks,max_uv_gap=maximum,epsilon=epsilon,atomic_nan_rejection=True,scope='Multilinear CPU UV extension only; costly up to256 integer corners, valid-corner bounded domain, no GPU/fullscene motion proof.');(p/'road-pair-uv-continuous-tests.json').write_text(json.dumps(report,indent=2));print(report)
