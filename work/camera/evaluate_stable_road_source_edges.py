from pathlib import Path
import ctypes as C,json,hashlib
p=Path('work/camera');rings=json.loads((p/'stable-road-projected-rings.json').read_text());triangles=json.loads((p/'stable-road-projected-inputs.json').read_text());geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);d=C.CDLL(str((p/'road-edge-continuous.dll').resolve()));fn=d.nf_road_edge_continuous;fn.argtypes=[C.c_void_p]*4;checks=[]
for ring,tri,road in zip(rings['checks'],triangles['checks'],geo['roads']):
 assert ring['surface']==tri['surface'];assert set(map(tuple,ring['ring']))==set(map(tuple,tri['triangles']))
 den=[(1<<road['source_attributes_header'][1])*.5,road['source_attributes_header'][2]*.5];vertices=[]
 for x,y,z,u,v in ring['ring']:
  q=16777216/z;vertices.append([x,y,0,q,u*q*den[0],v*q*den[1]])
 edges=[];short=0
 for i,a in enumerate(vertices):
  b=vertices[(i+1)%len(vertices)]
  if a[1]>b[1]:a,b=b,a
  h=b[1]-a[1]
  if h<1:short+=1;continue
  out=(C.c_double*4)();assert fn((C.c_double*6)(*a),(C.c_double*6)(*b),table,out)
  edges.append(dict(source_ring_edge=i,lower_endpoint=a,upper_endpoint=b,height=h,slopes=list(out)))
 checks.append(dict(surface=ring['surface'],native_path_ring_triangle_vertices_exact=True,continuous_edges=edges,short_edges_not_evaluated=short))
report=dict(result='PASS',checks=checks,ring_sha256=hashlib.sha256((p/'stable-road-projected-rings.json').read_bytes()).hexdigest(),scope='Owned native source world/camera/nearUV projected rings agree exactly with production triangle vertices; continuous slope component evaluated at source-derived endpoints. Short edges below1 excluded explicitly; horizontal clipping, interior sampling and GPU not yet covered.');(p/'stable-road-continuous-source-edges.json').write_text(json.dumps(report,indent=2));print(dict(result='PASS',edges=sum(len(c['continuous_edges']) for c in checks),short_edges=sum(c['short_edges_not_evaluated'] for c in checks)))
