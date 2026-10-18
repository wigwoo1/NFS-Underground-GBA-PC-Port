from pathlib import Path
from unittest.mock import patch
import random
import owned_sampled_road_camera as road
namespace={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-far-endpoints-20261006/road-camera-before.py').read_text(),namespace)
rng=random.Random(206);m=(16384,0,0,0,16384,0,0,0,16384,0,0,0);n=(*m[:9],10,3,20);poses=((1,0,0,0,1,0,0,0,1,0,0,0),(1,0,0,0,1,0,0,0,1,10,3,20))
world=tuple(v for _ in range(30) for v in (rng.randrange(-20000,20000),rng.randrange(-100,100),rng.randrange(1,20000)))
road._far_endpoint_projections.cache_clear()
with patch.object(road,'_rigid_depth',wraps=road._rigid_depth) as measured:
 for alpha in (0,.1,.25,.5,.75,.9,1):
  camera=(*poses[0][:9],10*alpha,3*alpha,20*alpha)
  assert road.sampled_road_far_depths(world,m,n,poses,camera,alpha)==namespace['sampled_road_far_depths'](world,m,n,poses,camera,alpha)
 assert measured.call_count==60+5*30,measured.call_count
assert road._far_endpoint_projections.cache_info().maxsize==64
print('PASS: exact original far depths at7 poses, endpoint terms once perworldpair, bounded64 cache')
