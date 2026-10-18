import random,struct,time,statistics,json
from pathlib import Path
from owned_portal_continuous import cells
from owned_continuous_wall_visibility import wall_near_delta
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
def prior(t,s,d,r):return cells((t,s,d),lambda t,s,d:(int(d)*((int(t)*r[int(s)])&0xffffffff))>>24)
rng=random.Random(20261006)
cases=[(rng.uniform(0,32766),rng.uniform(1,32766),rng.uniform(-2147483648,2147483647),r) for _ in range(10000)]
cases.extend((t,s,d,r) for t in (0,1,123.5,32766) for s in (1,2,255.25) for d in (-2147483648,-3,-1,0,1,2147483647))
for args in cases:assert prior(*args)==wall_near_delta(*args)
times={}
for name,fn in [('prior',prior),('specialized',wall_near_delta)]:
 batches=[]
 for _ in range(5):
  start=time.perf_counter_ns()
  for args in cases:fn(*args)
  batches.append((time.perf_counter_ns()-start)/1e6)
 times[name]=statistics.median(batches)
result=dict(result='PASS_EXACT_WALL_NEAR_CELLS',cases=len(cases),median_batch_ms=times,scope='Exact unsigned-factor wall arithmetic; component benchmark, not live cadence')
Path('work/camera/wall-near-cell-tests.json').write_text(json.dumps(result,indent=2));print(result)
