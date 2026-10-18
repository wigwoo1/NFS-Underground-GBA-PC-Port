import sys,json,time,statistics
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(source,'saved_scene_memory_fixture','exec'))
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_pointer_decode_candidate import ClosedSceneMemory as Candidate
from owned_complete_road_candidates import road_candidates
try:
 checks=[]
 for scene in scenes:
  a=Baseline(scene.graph,rom);b=Candidate(scene.graph,rom);assert a._ranges==b._ranges and a._starts==b._starts and a.owned_byte_count==b.owned_byte_count
  assert road_candidates(scene.graph,a)==road_candidates(scene.graph,b)
  for address,data in a._ranges:
   assert a.read(address,len(data))==b.read(address,len(data))==data
  checks.append(dict(ranges=len(a._ranges),owned_bytes=a.owned_byte_count))
 times={'baseline':[],'candidate':[]}
 for i in range(100):
  for label,cls in ([('baseline',Baseline),('candidate',Candidate)] if i%2==0 else [('candidate',Candidate),('baseline',Baseline)]):
   start=time.perf_counter_ns()
   for scene in scenes:cls(scene.graph,rom)
   times[label].append((time.perf_counter_ns()-start)/len(scenes)/1e6)
 out=dict(result='PASS_SAVED_SCENE_MEMORY_AND_ROAD_PARITY',checks=checks,medians_ms={k:statistics.median(v) for k,v in times.items()},scope='Two captured scenes: exact sparse ranges, all full-range reads and complete road candidates; alternating100construction timings. Not live/full4K performance or broad scene fidelity.')
 Path('work/camera/prototype-runs/scene-pointer-decode-parity.json').write_text(json.dumps(out,indent=2));print(out)
finally:history.close()
