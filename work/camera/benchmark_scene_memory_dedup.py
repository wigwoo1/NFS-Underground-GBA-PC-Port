import sys,json,time
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import statistics,random
from owned_closed_scene_memory import ClosedSceneMemory as Prior
from owned_scene_memory_dedup_candidate import ClosedSceneMemory as Candidate
# Warm imports and validate the entire sparse representation before timing.
for scene in scenes:
 a=Prior(scene.graph,rom);b=Candidate(scene.graph,rom)
 assert a._ranges==b._ranges and a._starts==b._starts and a.owned_byte_count==b.owned_byte_count
 r=random.Random(7761)
 for _ in range(500):
  start,data=r.choice(a._ranges);offset=r.randrange(len(data));length=r.randrange(1,min(100,len(data)-offset)+1)
  assert a.read(start+offset,length)==b.read(start+offset,length)
times={'prior':[],'candidate':[]}
for repeat in range(10):
 order=[('prior',Prior),('candidate',Candidate)]
 if repeat%2:order.reverse()
 for name,cls in order:
  begin=time.perf_counter_ns()
  for _ in range(50):
   for scene in scenes:cls(scene.graph,rom)
  times[name].append((time.perf_counter_ns()-begin)/1e6)
result=dict(result='PASS_EXACT_RANGES_AND_1000_READS',median_100_constructions_ms={k:statistics.median(v) for k,v in times.items()},range_ms={k:[min(v),max(v)] for k,v in times.items()},scope='Actual two captured scenes; component construction only, not live rendering')
Path('work/camera/scene-memory-dedup-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
