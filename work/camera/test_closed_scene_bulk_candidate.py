import sys,time,json,statistics,random
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(source,'actual_saved_scene_setup','exec'))
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_bulk_candidate import ClosedSceneMemory as Candidate
try:
 for scene in scenes:
  a=Baseline(scene.graph,rom);b=Candidate(scene.graph,rom)
  assert (a._ranges,a._starts,a.owned_byte_count)==(b._ranges,b._starts,b.owned_byte_count)
  rng=random.Random(4321)
  for _ in range(1000):
   start,data=rng.choice(a._ranges);offset=rng.randrange(len(data));size=rng.randrange(1,min(128,len(data)-offset)+1);assert a.read(start+offset,size)==b.read(start+offset,size)
 times={'baseline':[],'candidate':[]}
 for repeat in range(8):
  order=[('baseline',Baseline),('candidate',Candidate)]
  if repeat%2:order.reverse()
  for name,cls in order:
   begin=time.perf_counter_ns()
   for _ in range(30):
    for scene in scenes:cls(scene.graph,rom)
   times[name].append((time.perf_counter_ns()-begin)/1e6)
 result=dict(result='PASS_EXACT_SPARSE_RANGES_2000_READS',median_60_constructions_ms={k:statistics.median(v) for k,v in times.items()},scope='Two real saved scenes only; no conflict/missing/ROM overlay adversarial test yet, no live speedup or full4K pixel qualification.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/bulk-memory-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
finally:history.close()
