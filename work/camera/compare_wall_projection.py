"""Compare recovered world/camera projection against retained wall edges."""
from pathlib import Path
import json,struct,math
p=Path('outputs/nfsug-native-renderer/camera-research')
audit=json.loads((p/'native-wall-invocation-audit.json').read_text())
world=json.loads((p/'native-world-audit.json').read_text())
b=Path('work/camera/prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-native-scene.bin').read_bytes()
offset,size=struct.unpack_from('<II',b,36);models=b[offset:offset+size]
if struct.unpack_from('<I',models)[0]==0x314c4d4e:
 offset,size=struct.unpack_from('<II',models,8);model=models[offset:offset+size]
else:model=models
assert struct.unpack_from('<I',model)[0]==0x324d464e
cx,cy,scale=struct.unpack_from('<3d',model,24)
px,py,pz,x,y,z,w=struct.unpack_from('<7d',model,48)
assert all(math.isfinite(t) for t in (cx,cy,scale,px,py,pz,x,y,z,w)) and abs(x*x+y*y+z*z+w*w-1)<1e-6
rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
results=[]
for region in audit['suspect_regions']:
 if region['pose']!='sampled':continue
 for edge in region['edges']:
  surface=next(s for s in world['surfaces'] if s['source']==edge['source'])
  points=[]
  for vertex in surface['vertices']:
   delta=[v-o for v,o in zip(vertex,(px,py,pz))]
   camera=[sum(a*d for a,d in zip(row,delta)) for row in rows]
   assert all(math.isfinite(t) for t in camera) and camera[2]!=0
   points.append(dict(camera=camera,projected=[cx+scale*camera[0]/camera[2],cy+scale*camera[1]/camera[2]]))
  original=edge['projected_xy_depth'];left,right=original[:2]
  # Original wall_project sorts only horizontal endpoints for reverse-facing
  # walls. Depth and vertical endpoints retain the source order.
  if edge['flags']&2:left,right=right,left
  expected=((left,original[4]),(right,original[5]),(right,original[7]),(left,original[6]))
  error=max(abs(a-b) for point,pair in zip(points,expected) for a,b in zip(point['projected'],pair))
  assert error<=1, (edge['source'],error)
  results.append(dict(source=edge['source'],native_points=points,original_sampled_edge=original,max_projection_error=error,near_crossing=any(t['camera'][2]<64 for t in points)))
report=dict(result='COMPARED',camera=[px,py,pz,x,y,z,w],projection=[cx,cy,scale],walls=results,scope='Native recovered world geometry projected with packet quaternion versus reconstructed original sampled wall edges; no image polygon matching. Quantization and reciprocal approximation are expected.')
(p/'native-wall-projection-comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(results,indent=2))
