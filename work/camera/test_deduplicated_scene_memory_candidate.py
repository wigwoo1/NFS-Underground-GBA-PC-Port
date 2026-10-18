from pathlib import Path
import json,time,statistics
from owned_closed_scene_memory import ClosedSceneMemory
from owned_deduplicated_scene_memory_candidate import DeduplicatedSceneMemory
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns);env=ns['env'];rom=env['rom'];scenes=env['scenes'];times=[[],[]];counts=[]
for iteration in range(32):
 for index in (iteration%2,1-iteration%2):
  cls=(ClosedSceneMemory,DeduplicatedSceneMemory)[index];begin=time.perf_counter_ns();memories=[cls(scene.graph,rom) for scene in scenes];times[index].append(time.perf_counter_ns()-begin)
  if index==0:baseline=memories
  else:candidate=memories
 if iteration==0:
  for a,b in zip(baseline,candidate):
   assert a._ranges==b._ranges and a._starts==b._starts and a.owned_byte_count==b.owned_byte_count
   for address,data in a._ranges:
    assert a.read(address,len(data))==b.read(address,len(data))==data
   counts.append(dict(raw=b.raw_ranges,unique=b.unique_ranges,duplicates=b.raw_ranges-b.unique_ranges))
summary=[dict(median_ms=statistics.median(v)/1e6,mean_ms=statistics.mean(v)/1e6) for v in times]
out=dict(result='PASS_EXACT_DEDUPLICATED_MEMORY',endpoint_counts=counts,baseline=summary[0],candidate=summary[1],pairs=32,scope='Controlled alternating actual two source endpoints, all sparse ranges and contained reads exact. Candidate not installed; no live performance claim.')
Path('outputs/nfsug-native-renderer/camera-research/deduplicated-scene-memory-20261009.json').write_text(json.dumps(out,indent=2));print(out)
