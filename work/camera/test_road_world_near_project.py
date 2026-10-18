"""World-derived near crossings using original reciprocal arithmetic."""
from pathlib import Path
import json,struct,ctypes as C
p=Path('work/camera');events=json.loads((p/'stable-original-road-source.json').read_text())['roads'];geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());joins=json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks'];maps=json.loads((p/'stable-road-emission-source-map.json').read_text())['checks']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();raw=rom[0x627700:0x647700];table=struct.unpack('<32768I',raw);buf=C.create_string_buffer(raw)
cam=C.CDLL(str((p/'road-camera-continuous.dll').resolve())).nf_road_camera_continuous;cam.argtypes=[C.c_void_p]*3
project=C.CDLL(str((p/'road-point-project-continuous.dll').resolve())).nf_road_point_project_continuous;project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
si=lambda x:((x+2**31)%2**32)-2**31
half=lambda x:((x+32768)%65536)-32768
checks=[]
for e in events:
 j=next(j for j in joins if j['source']==e['source']);g=next(g for g in geo['roads'] if g['surface']==j['surface']);mapping=next(m for m in maps if m['source']==e['source']);m=(C.c_int32*12)(*struct.unpack('<12i',bytes.fromhex(e['blocks']['2']['hex'])));points=[]
 for v in g['vertices']:
  out=(C.c_double*3)();assert cam((C.c_double*3)(*v),m,out);points.append(list(map(int,out)))
 for row in mapping['mapping']:
  if not row['near_generated']:continue
  a=row['source_edge'];b=(a+1)%len(points);start=points[a][2]<64;target=a if start else b;point=points[target].copy();attrs=g['source_attributes'][target].copy();delta=abs(points[b][2]-points[a][2]);factor=((64-point[2])*table[delta])&0xffffffff
  def adjust(x,y):return si(si(y-x)*factor>>24)
  point[0]=half(point[0]+(1 if start else -1)*adjust(points[a][0],points[b][0]));point[1]=si(point[1]+(1 if start else -1)*adjust(points[a][1],points[b][1]));point[2]=64
  for k in range(2):attrs[k]=si(attrs[k]+(1 if start else -1)*adjust(g['source_attributes'][a][k],g['source_attributes'][b][k]))
  out=(C.c_double*5)();head=g['source_attributes_header'];assert project((C.c_double*3)(*point),(C.c_int32*2)(*attrs),head[1],head[2],(C.c_int32*3)(120,87,128),buf,out)
  expected=[row['six_words'][k] for k in (0,1,3,4,5)];assert list(out)==expected,(point,attrs,list(out),expected)
  checks.append(dict(source=e['source'],edge=a,point=point,attrs=attrs,projected=list(out)))
assert len(checks)==4
report=dict(result='PASS',near_generated_vertices=4,checks=checks,scope='Independent world-derived original integer near-crossing arithmetic and component projection. Fractional clipping extension, packet/live renderer integration and motion remain unverified.')
(p/'road-world-near-project-tests.json').write_text(json.dumps(report,indent=2));print(report)
