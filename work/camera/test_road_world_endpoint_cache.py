"""Exact road projection and rejection parity with saved uncached implementation."""
import random,json
from pathlib import Path
from owned_sampled_road_camera import sampled_road_camera,_world_endpoint_projections
checkpoint=Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-world-endpoint-reuse-20261006')
reference={};exec(compile((checkpoint/'before-road.py').read_text(),'reference','exec'),reference)
rng=random.Random(91);checks=0;rejections=0
for i in range(1000):
 world=tuple(float(rng.randrange(-40000,40000)) for _ in range(12))
 ma=(16384,0,0,0,16384,0,0,0,16384,*[rng.randrange(-200,200) for _ in range(3)])
 mb=(*ma[:9],*[rng.randrange(-200,200) for _ in range(3)])
 a=(*[x/16384 for x in ma[:9]],*[float(x) for x in ma[9:]]);b=(*a[:9],*[float(x) for x in mb[9:]])
 alpha=(0,1,.25,.5,.75)[i%5];camera=(*a[:9],*[a[k]+(b[k]-a[k])*alpha for k in range(9,12)])
 outcomes=[]
 for fn in (reference['sampled_road_camera'],sampled_road_camera):
  try:outcomes.append(('ok',fn(world,ma,mb,(a,b),camera,alpha)))
  except ValueError as e:outcomes.append(('error',str(e)))
 assert outcomes[0]==outcomes[1];checks+=1;rejections+=outcomes[0][0]=='error'
for bad_world,bad_alpha in (((.5,0.,0.),.5),((float('nan'),0.,0.),.5),((0.,0.,0.),-1),((0.,0.),.5)):
 outcomes=[]
 for fn in (reference['sampled_road_camera'],sampled_road_camera):
  try:outcomes.append(('ok',fn(bad_world,ma,mb,(a,b),camera,bad_alpha)))
  except ValueError as e:outcomes.append(('error',str(e)))
 assert outcomes[0]==outcomes[1] and outcomes[0][0]=='error';checks+=1;rejections+=1
assert _world_endpoint_projections.cache_info().currsize<=64
result=dict(exact_cases=checks,exact_rejections=rejections,bounded_capacity=64)
(checkpoint/'random-parity.json').write_text(json.dumps(result,indent=2));print(result)
