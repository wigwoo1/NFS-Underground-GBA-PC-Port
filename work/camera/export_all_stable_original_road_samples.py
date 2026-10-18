"""Source-geometric road UV sampling, never polygon matching or reconstruction."""
from pathlib import Path
import json,struct,ctypes as C,hashlib,math,sys
policy=int(sys.argv[1]) if len(sys.argv)>1 else 0;assert policy in (0,1,2,3,4,5,6)
p=Path('work/camera');geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());projected=json.loads((p/('stable-road-projected-inputs.json' if policy==0 else f'stable-road-projected-policy-{policy}.json')).read_text());b=(p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==geo['source_sha256'];h=struct.unpack_from('<8I',b)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x647700];d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_perspective_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
checks=[]
def cross(a,c,x,y):return (c[0]-a[0])*(y-a[1])-(c[1]-a[1])*(x-a[0])
def sample(tri,x,y,affine):
 a,c,e=tri;area=cross(a,c,e[0],e[1])
 if abs(area)<1e-10:return None
 weights=[cross(c,e,x,y)/area,cross(e,a,x,y)/area,cross(a,c,x,y)/area]
 if min(weights)<-1e-9:return None
 q=[1 if affine else 1/v[2] for v in tri];den=sum(w*z for w,z in zip(weights,q))
 return tuple(sum(w*z*v[k] for w,z,v in zip(weights,q,tri))/den for k in (3,4))
for i in range(h[3]):
 pas,ordinal,off,size=struct.unpack_from('<4I',b,32+i*16);asset=b[off:off+size];head=struct.unpack_from('<10I',asset);texture=asset[head[9]:];surface=geo['order'][ordinal];road=next(r for r in geo['roads'] if r['surface']==surface);triangles=next(r['triangles'] for r in projected['checks'] if r['surface']==surface);original={}
 for j in range(head[5]):
  s=struct.unpack_from('<20I',asset,40+j*80);runs=[]
  if s[2]==0x03003190:
   out=C.create_string_buffer(2048);final=C.create_string_buffer(64);n=C.c_uint();assert fn(struct.pack('<16I',*s[4:20]),table,out,32,C.byref(n),final);runs=[struct.unpack_from('<16I',out.raw,r*64) for r in range(n.value)]
  else:runs=[s[4:20]]
  at=0
  for run in runs:
   u,v=run[8:10]
   for k in range(run[7]):
    u&=run[1];v&=run[2];address=2*((u>>16)+((v>>16)<<run[0]));assert address+2<=len(texture)
    page=0x0600a000 if s[0]>=0x0600a000 else 0x06000000
    for dup in range(s[3]+1):
     for lane in range(2):
      dest=s[0]-page+at*2+dup*240+lane
      if dest<38400:original[dest%240,dest//240]=texture[address+lane]
    u=(u+run[10])&0xffffffff;v=(v+run[11])&0xffffffff;at+=1
 records=b''.join(struct.pack('<IB',y*240+x,index) for (x,y),index in sorted(original.items(),key=lambda item:item[0][1]*240+item[0][0]));(p/f'stable-road-{ordinal}-all-original-samples.bin').write_bytes(records);checks.append(dict(ordinal=ordinal,pixels=len(original),samples_sha256=hashlib.sha256(records).hexdigest()))
report=dict(result='PASS',checks=checks,scope='All original road span pixels including row duplication and spill; no native coverage restriction. Recovered perspective subdivision exact component, immutable original texture payload. Diagnostic reference only.');(p/'stable-road-all-original-samples.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
