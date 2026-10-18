import random
from pathlib import Path
from types import SimpleNamespace
namespace={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-rigid-depth-reuse-20261006/cached-camera-candidate.py').read_text(),namespace)
current=SimpleNamespace(**namespace)
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-rigid-depth-reuse-20261006/camera-before.py').read_text(),prior)
r=random.Random(61006);current._cached_rigid_depth.cache_clear()
for _ in range(10000):
 point=tuple(r.uniform(-1e10,1e10) for _ in range(3));pose=tuple(r.uniform(-10,10) for _ in range(12))
 assert current._rigid_depth(point,pose)==prior['_rigid_depth'](point,pose)
 before=current._cached_rigid_depth.cache_info()
 assert current._rigid(point,pose)==prior['_rigid'](point,pose)
 after=current._cached_rigid_depth.cache_info();assert after.hits==before.hits+1 and after.currsize<=256
print('PASS:10000 exact compensated depth/full rigid tuples,shared cache hits,bounded256entries')
