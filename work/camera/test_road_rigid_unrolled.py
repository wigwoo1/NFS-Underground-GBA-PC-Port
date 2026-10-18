import random,struct,time,statistics,json
from pathlib import Path
from owned_sampled_road_camera import _rigid
ns={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-rigid-unrolled-20261006/before.py').read_text(),ns);before=ns['_rigid'];r=random.Random(72813);inputs=[(tuple(r.uniform(-32768,32767) for _ in range(3)),tuple(r.uniform(-100,100) for _ in range(12))) for _ in range(10000)];inputs += [((z,z,z),(z,)*12) for z in (0.0,-0.0)]
for p,m in inputs:assert struct.pack('<3d',*before(p,m))==struct.pack('<3d',*_rigid(p,m))
times={before:[],_rigid:[]}
for i in range(10):
 for fn in ((before,_rigid) if i%2==0 else (_rigid,before)):
  start=time.perf_counter_ns()
  for p,m in inputs:fn(p,m)
  times[fn].append(time.perf_counter_ns()-start)
out=dict(samples=len(inputs),bit_exact=True,before_median_ms=statistics.median(times[before])/1e6,after_median_ms=statistics.median(times[_rigid])/1e6)
Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-rigid-unrolled-20261006/comparison.json').write_text(json.dumps(out,indent=2));print('PASS',out)
