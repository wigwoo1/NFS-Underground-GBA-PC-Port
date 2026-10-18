from pathlib import Path
import ctypes as C,json,struct,math
p=Path('work/camera');events=json.loads((p/'stable-original-road-source.json').read_text())['roads'];refs=json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks']
d=C.CDLL(str((p/'road-camera-continuous.dll').resolve()));f=d.nf_road_camera_continuous;f.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_int32),C.POINTER(C.c_double)]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def run(v,m):
 out=(C.c_double*3)(99,99,99);ok=f((C.c_double*3)(*v),m,out);return ok,list(out)
checks=0;continuity=0;largest=0
for e in events:
 b={int(k):bytes.fromhex(v['hex']) for k,v in e['blocks'].items()};m=(C.c_int32*12)(*struct.unpack('<12i',b[2]));ref=next(r for r in refs if r['event']==e['event']);face=b[42] or bytes(20)
 for j,row in enumerate(ref['vertices']):
  s=b[5][j*68:(j+1)*68];off=b[10+j] or bytes(32);v=[i(s,0)+h(off,0),h(s,56)+h(off,6)+h(face,6),i(s,4)+h(off,2)]
  ok,out=run(v,m);assert ok and out==row['original_camera'],(v,out,row);checks+=1
  for k in (0,2):
   a=v.copy();c=v.copy();a[k]-=1e-8;c[k]+=1e-8
   aa=run(a,m)[1];cc=run(c,m)[1];delta=max(abs(x-y) for x,y in zip(aa,cc));largest=max(largest,delta);assert delta<.01;continuity+=1
for v in ([float('nan'),0,0],[2**31,0,0],[0,0,float('inf')]):
 ok,out=run(v,m);assert not ok and out==[99]*3
report=dict(result='PASS',integer_source_vertices=checks,two_sided_cell_checks=continuity,max_delta=largest,atomic_invalid_checks=3,scope='Fixed captured original matrix component only; snapshot matrix provenance and moving matrix interpolation remain unverified.')
(p/'stable-road-camera-continuous-test.json').write_text(json.dumps(report,indent=2));print(report)
