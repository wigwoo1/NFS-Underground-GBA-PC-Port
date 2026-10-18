import sys,json,struct,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'savedscene','exec'))
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_scene_range_dedup_candidate import ClosedSceneMemory as Candidate

import time,statistics,gc
samples={'baseline':[],'candidate':[]}
try:
 for scene in scenes:
  for cls in (Baseline,Candidate):
   for i in range(8):cls(scene.graph,rom)
 gc_enabled=gc.isenabled();gc.disable()
 try:
  for iteration in range(120):
   order=[('baseline',Baseline),('candidate',Candidate)]
   if iteration%2:order.reverse()
   for label,cls in order:
    begin=time.perf_counter_ns()
    for scene in scenes:cls(scene.graph,rom)
    samples[label].append((time.perf_counter_ns()-begin)/2e6)
 finally:
  if gc_enabled:gc.enable()
 medians={k:statistics.median(v) for k,v in samples.items()}
 out=dict(result='COMPLETE_MATCHED_SCENE_MEMORY_BENCHMARK',iterations=120,scenes=2,median_ms=medians,candidate_to_baseline_ratio=medians['candidate']/medians['baseline'],samples_ms=samples,scope='Alternating-order same-input in-process constructors, warmed and GC disabled equally. Limited two saved scenes; no live cadence claim.')
 Path('work/camera/prototype-runs/scene-range-dedup-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print(out['median_ms'],out['candidate_to_baseline_ratio'])
finally:history.close()
