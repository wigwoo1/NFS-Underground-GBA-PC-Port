"""Enumerate source-world near-plane cases in complete multimodel packets."""
from pathlib import Path
import json,struct,math
p=Path('outputs/nfsug-native-renderer/camera-research');exports=json.loads((p/'source-order-multimodel-exports.json').read_text())['exports'];rows=[]
for e in exports:
 b=Path(e['path']).read_bytes();sections=[]
 for i in range(5):
  _,offset,size=struct.unpack_from('<3I',b,32+i*12);sections.append(b[offset:offset+size])
 models=sections[0];offset,length=struct.unpack_from('<2I',models,8);m=models[offset:offset+length];px,py,pz,x,y,z,w=struct.unpack_from('<7d',m,48);rotation=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 world=sections[1];n=struct.unpack_from('<I',world,4)[0];pos=8;surfaces=[]
 for i in range(n):
  count,width,height=struct.unpack_from('<3I',world,pos);pos+=12;points=[struct.unpack_from('<3d',world,pos+j*24) for j in range(count)];pos+=count*40+width*height*4;depths=[sum(a*(v-o) for a,v,o in zip(rotation[2],point,(px,py,pz))) for point in points];assert all(math.isfinite(t) for t in depths);kind,state,source,base,_=struct.unpack_from('<5I',sections[4],8+i*20);crossing=any(t<64 for t in depths) and any(t>=64 for t in depths)
  if crossing:surfaces.append(dict(index=i,kind=kind,source=hex(source),min_depth=min(depths),max_depth=max(depths)))
 rows.append(dict(identity=e['identity'],crossing_surfaces=surfaces,surface_count=n))
(p/'multimodel-near-plane-cases.json').write_text(json.dumps(dict(result='ENUMERATED',scenes=rows,scope='Finite source geometry and actual near64 crossings. Successful render does not prove clipped coverage or source UV interpolation.'),indent=2));print('crossings',sum(len(r['crossing_surfaces']) for r in rows))
