"""Compare isolated GPU sign RGB with continuous CPU sampling at native centers."""
import hashlib,json,math,os,struct,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
capture_path=Path(sys.argv[1]); projection_path=Path(sys.argv[2]); sources_path=Path(sys.argv[3])
projection=json.loads(projection_path.read_text()); sources=json.loads(sources_path.read_text())
rows={tuple(r['identity'][2:]):r for r in sources['original_endpoints']}
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
checks=[]
def triangulate(points):
 """Mirror renderer ear selection on owned projected vertices, never screen matching."""
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 ids=list(range(len(points))); sign=1 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))>=0 else -1; triangles=[]
 while len(ids)>=3:
  found=False
  for j in range(len(ids)):
   prev=(j-1)%len(ids); nex=(j+1)%len(ids); a,b,c=[points[ids[k]] for k in (prev,j,nex)]
   if cross(a,b,c)*sign<1e-8:continue
   if any(cross(a,b,points[ids[k]])*sign>1e-8 and cross(b,c,points[ids[k]])*sign>1e-8 and cross(c,a,points[ids[k]])*sign>1e-8 for k in range(len(ids)) if k not in (prev,j,nex)):continue
   triangles.append(tuple(ids[k] for k in (prev,j,nex))); ids.pop(j); found=True; break
  assert found
 return triangles
for pose in projection['checks']:
 row=rows[tuple(pose['interval'])]; packet=Path(row['path']); data=packet.read_bytes()
 assert hashlib.sha256(data).hexdigest()==row['sha256']
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))}
 world=sections[2]; position=8; selected=[]
 for i in range(struct.unpack_from('<I',world,4)[0]):
  n,w,h=struct.unpack_from('<3I',world,position)
  kind,_,source,_,_=struct.unpack_from('<5I',sections[5],8+i*20)
  if kind==2 and source==0x08574c3c:
   assert n==4 and w==h==64
   selected.append((i,np.frombuffer(world[position+12+n*40:position+12+n*40+w*h*4],np.uint8).reshape(h,w,4)))
  position+=12+n*40+w*h*4
 assert len(selected)==1
 ordinal,texture=selected[0]; target=p/'prototype-runs'/f"sign-gpu-{pose['interval'][0]}.ppm"
 settings=dict(env,NF_ENDPOINT_COMMANDS=str(ordinal))
 subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),str(packet),str(target)],env=settings,check=True,capture_output=True)
 image=np.asarray(Image.open(str(target)+'-0.ppm')); assert image.shape==(2160,3840,3)
 baseline_target=target.with_name(target.stem+'-background.ppm')
 subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),str(packet),str(baseline_target)],env=dict(env,NF_ENDPOINT_COMMANDS='4294967200'),check=True,capture_output=True)
 baseline=np.asarray(Image.open(str(baseline_target)+'-0.ppm'))
 points=[list(c)+list(uv) for c,uv in zip(pose['native_corners'],[(0,0),(2,0),(2,1),(0,1)])]
 triangles=triangulate(points); assert triangles==[(3,0,1),(3,1,2)]
 counts=dict(inside=0,opaque=0,rgb_equal=0,rgb_different=0,transparent=0,transparent_background_equal=0,transparent_background_different=0,outside=0,outside_background_different=0); examples=[]
 for y in range(160):
  py=int((y+.5)*13.5); sy=(py+.5)/13.5
  for x in range(240):
   px=int(300+(x+.5)*13.5); sx=(px-300+.5)/13.5; uv=None
   for ids in triangles:
    a,b,c=[points[i] for i in ids]; den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    wa=((b[1]-c[1])*(sx-c[0])+(c[0]-b[0])*(sy-c[1]))/den; wb=((c[1]-a[1])*(sx-c[0])+(a[0]-c[0])*(sy-c[1]))/den; wc=1-wa-wb
    if min(wa,wb,wc)<0:continue
    q=wa/a[2]+wb/b[2]+wc/c[2]; uv=[sum(t[k]*weight/t[2] for t,weight in zip((a,b,c),(wa,wb,wc)))/q for k in (3,4)]; break
   if uv is None:
    counts['outside']+=1; counts['outside_background_different']+=int(not np.array_equal(image[py,px],baseline[py,px])); continue
   counts['inside']+=1; tx=math.floor(uv[0]*64)%64; ty=math.floor(uv[1]*64)%64; expected=texture[ty,tx]
   if not expected[3]:
    counts['transparent']+=1; equal=np.array_equal(image[py,px],baseline[py,px]); counts['transparent_background_equal' if equal else 'transparent_background_different']+=1
    if not equal and len(examples)<12:examples.append(dict(x=x,y=y,physical_pixel=[px,py],uv=uv,texel=[tx,ty],expected_background=baseline[py,px].tolist(),actual=image[py,px].tolist()))
    continue
   counts['opaque']+=1; equal=np.array_equal(image[py,px],expected[:3]); counts['rgb_equal' if equal else 'rgb_different']+=1
   if not equal and len(examples)<12:examples.append(dict(x=x,y=y,texel=[tx,ty],expected=expected[:3].tolist(),actual=image[py,px].tolist()))
 checks.append(dict(interval=pose['interval'],packet_sha256=row['sha256'],command=ordinal,triangles=triangles,counts=counts,differences=examples))
assert len(checks)==6 and all(c['counts']['opaque']>0 for c in checks)
out=capture_path.with_name(capture_path.stem.replace('-verification','-sign-gpu-sampling-triangulated')+'.json')
out.write_text(json.dumps(dict(result='MEASURED',projection_sha256=hashlib.sha256(projection_path.read_bytes()).hexdigest(),renderer_sha256=hashlib.sha256((p/'endpoint-scene-road-order-preview.exe').read_bytes()).hexdigest(),checks=checks,scope='Isolated actual GPU RGB at exact 4K physical pixel centers versus CPU continuous perspective UV sampling of owned packet textures; transparent/outside pixels compared to same-packet background-only render. Identical-color writes remain invisible. Six endpoint samples do not prove full-scene fidelity, motion or scanout.'),indent=2))
print(json.dumps(checks))
