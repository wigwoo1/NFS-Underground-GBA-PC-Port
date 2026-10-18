from pathlib import Path
import random,time,statistics,json,struct
from owned_portal_continuous import projection_depth,coordinate_at_depth
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/projection-even-cell-20261006/projection-before.py').read_text(),prior)
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(603)
cases=[(rng.uniform(-32768,32767),projection_depth(rng.uniform(1,32765),rng.choice((128,256,512,65535)),r),rng.randrange(-32768,32768)) for _ in range(10000)]
for args in cases:assert coordinate_at_depth(*args)==prior['coordinate_at_depth'](*args)
from unittest.mock import patch
import owned_portal_continuous as current
counts={};timings={}
for name,fn,owner in (('prior',prior['coordinate_at_depth'],prior),('even_cell',coordinate_at_depth,current.__dict__)):
 original=owner['signed32'];count=[0]
 def measured(v):count[0]+=1;return original(v)
 owner['signed32']=measured
 for args in cases:fn(*args)
 owner['signed32']=original;counts[name]=count[0]
 rounds=[]
 for _ in range(7):
  begin=time.perf_counter_ns()
  for args in cases:fn(*args)
  rounds.append((time.perf_counter_ns()-begin)/1e6)
 timings[name]=statistics.median(rounds)
result=dict(result='PASS_EXACT',cases=len(cases),signed32_calls=counts,median_batch_ms=timings,scope='Deterministic projection CPU microbenchmark,7 rounds; no live timing claim')
Path('work/camera/even-projection-cell-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
