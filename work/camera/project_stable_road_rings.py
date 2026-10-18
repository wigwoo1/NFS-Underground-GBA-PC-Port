from pathlib import Path
import ctypes as C,json,struct,math,hashlib,sys
policy=int(sys.argv[1]) if len(sys.argv)>1 else 0;assert policy in (0,1,2,3,4,5,6)
p=Path('work/camera');r=json.loads((p/'stable-road-geometric-inputs.json').read_text());d=C.CDLL(str((p/'road-project-component.dll').resolve()));fn=d.nf_road_project_ring_component;fn.argtypes=[C.c_void_p]*3+[C.c_uint]+[C.c_void_p]*5+[C.c_uint]
class Vertex(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('u',C.c_double),('v',C.c_double)]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);bundle=(p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin').read_bytes();assert hashlib.sha256(bundle).hexdigest()==r['source_sha256']
h=struct.unpack_from('<8I',bundle);ordered=bundle[h[5]:h[5]+h[6]];oh=struct.unpack_from('<16I',ordered);packet=ordered[oh[12]:oh[12]+oh[13]];tag,offset,size=struct.unpack_from('<3I',packet,32);model=packet[offset:offset+size];assert tag==1 and model[:4]==b'NFM2'
projection=(C.c_double*3)(*struct.unpack_from('<3d',model,24));checks=[]
for road in r['roads']:
 command=r['order'].index(road['surface']);camera=(C.c_double*7)(*r['cameras'][command]);n=len(road['vertices']);world=(C.c_double*(n*3))(*(v for row in road['vertices'] for v in row));uv=(C.c_double*(n*2))(*(v for row in road['uv'] for v in row));head=road['source_attributes_header'];attrs=road['source_attributes'];raw=struct.pack('<6I66i',*head,*[v for row in attrs for v in row],*([0]*(64-len(attrs)*2)));out=(Vertex*192)();count=C.c_uint();assert fn(camera,world,uv,n,raw,table,projection,out,C.byref(count),policy);assert count.value>=3
 ring=[[getattr(out[i],k) for k in ('x','y','z','u','v')] for i in range(count.value)];assert all(math.isfinite(v) for row in ring for v in row) and all(row[2]>=64 for row in ring)
 checks.append(dict(surface=road['surface'],command=command,source_vertices=n,ring_vertices=count.value,ring=ring))
report=dict(policy=policy,result='PASS',serial=r['serial'],projection=list(projection),checks=checks,component_sha256=hashlib.sha256((p/'road-project-component.dll').read_bytes()).hexdigest(),scope='Exact production rigid transform, corrected near clip before triangulation executed on retained stable input. Original projection from retained NFM2. Source ring export only; not GPU raster or original pixel parity; Selected clipping policy is explicit; mode1 linear diagnostic, mode2 continuous near-limit.')
(p/('stable-road-projected-rings.json' if policy==0 else f'stable-road-projected-policy-{policy}.json')).write_text(json.dumps(report,indent=2));print(dict(result='PASS',roads=len(checks),ring_vertices=sum(c['ring_vertices'] for c in checks)))




