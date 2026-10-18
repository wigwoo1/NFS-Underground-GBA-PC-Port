from pathlib import Path
import json,struct,ctypes as C,math
p=Path('work/camera');original=json.loads((p/'stable-original-road-source.json').read_text());native=json.loads((p/'stable-road-geometric-inputs.json').read_text());d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_rigid_scene_sample;fn.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def si(x):return ((x+2**31)%2**32)-2**31
def half(x):return ((x+32768)%65536)-32768
checks=[];used=set()
for event in original['roads']:
 b={int(k):(v['address'],bytes.fromhex(v['hex'])) for k,v in event['blocks'].items()};desc=b[4][1];src=b[5][1];n=u(desc,2);cam=struct.unpack('<12i',b[2][1]);face=b[42][1] or bytes(20);world=[];attrs=[]
 for j in range(n):
  s=src[j*68:(j+1)*68];off=b[10+j][1] or bytes(32);world.append([i(s,0)+h(off,0),h(s,56)+h(off,6)+h(face,6),i(s,4)+h(off,2)]);attrs.append([i(s,32),i(s,36)])
 matches=[r for r in native['roads'] if r['vertices']==world and r['source_attributes']==attrs];assert len(matches)==1,(event['event'],len(matches));road=matches[0];assert road['surface'] not in used;used.add(road['surface']);command=native['order'].index(road['surface']);camera=(C.c_double*7)(*native['cameras'][command]);fixed=(C.c_double*7)(0,0,0,0,0,0,1);vertices=(C.c_double*(3*n))(*(v for row in world for v in row));out=(C.c_double*(3*n))();assert fn(camera,camera,fixed,fixed,0,vertices,n,out)
 errors=[];rows=[]
 for j,(wx,wy,wz) in enumerate(world):
  x=wx+cam[9];z=wz+cam[11];expected=[half(si(x*cam[0]+z*cam[6])>>14),wy+cam[10],half(si(x*cam[2]+z*cam[8])>>14)];actual=list(out[j*3:j*3+3]);error=[a-c for a,c in zip(actual,expected)];errors.append(max(map(abs,error)));rows.append(dict(vertex=j,original_camera=expected,native_camera=actual,error=error))
 checks.append(dict(event=event['event'],source=event['source'],surface=road['surface'],command=command,source_vertices_exact=True,raw_attributes_exact=True,max_camera_coordinate_error=max(errors),vertices=rows))
assert len(used)==3
report=dict(result='SOURCE_JOINS_EXACT',checks=checks,scope='Exact ordered world vertex/rawUV source joins; original Q14 planar camera arithmetic versus native quaternion rigid transform at source corners. No projected polygon matching. Difference includes original truncation/matrix normalization; no GPU or final-scene parity claim.')
(p/'stable-road-source-transform-comparison.json').write_text(json.dumps(report,indent=2));print([{k:v for k,v in c.items() if k!='vertices'} for c in checks])
