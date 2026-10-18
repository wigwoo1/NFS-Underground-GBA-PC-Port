from pathlib import Path
import random,struct,time,statistics,json
from owned_portal_continuous import near_delta
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/near-cell-specialization-20261006/projection-before.py').read_text(),prior)
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(610064)
cases=[(rng.uniform(0,32766),rng.uniform(1,32766),rng.uniform(-2147483648,2147483647),r) for _ in range(10000)]
cases += [(t,d,x,r) for t in (0,1,123.5) for d in (1,2,255.25) for x in (-3,-2,-1,0,1,2147483647)]
for args in cases:assert near_delta(*args)==prior['near_delta'](*args)
times={}
for name,fn in (('prior',prior['near_delta']),('specialized',near_delta)):
 values=[]
 for _ in range(5):
  begin=time.perf_counter_ns()
  for args in cases:fn(*args)
  values.append((time.perf_counter_ns()-begin)/1e6)
 times[name]=statistics.median(values)
result=dict(result='PASS_EXACT_NEAR_CELLS',cases=len(cases),median_batch_ms=times,scope='Seeded fractional/integer/signed-wrap projection CPU component; not live timing')
Path('work/camera/near-cell-specialization-tests.json').write_text(json.dumps(result,indent=2));print(result)
