import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
import owned_motion_visibility as v
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[];timings=[[],[]]
class Cached(v.PortalMotionPair):cache_topology=True
for left,right in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(left['graph']).read_bytes());b=ClosedGraph.decode(Path(right['graph']).read_bytes());motion=PreparedMotionPair(Path(left['regenerated']).read_bytes(),Path(right['regenerated']).read_bytes())
 ordinary=v.PortalMotionPair(a.graph,b.graph,table,motion);candidate=Cached(a.graph,b.graph,table,motion)
 alphas=[i/18 for i in range(19)]
 for repeat in range(3):
  results={}
  for mode in (repeat%2,1-repeat%2):
   pair=(ordinary,candidate)[mode];pair._samples.clear();start=time.perf_counter_ns();results[mode]=[pair.sample(x) for x in alphas];timings[mode].append((time.perf_counter_ns()-start)/1e6)
  assert results[0]==results[1]
 assert len(candidate._samples)==8
 for invalid in (float('nan'),-1,2):
  try:candidate.sample(invalid)
  except ValueError:pass
  else:raise AssertionError('Invalid alpha accepted')
 checks.append(dict(older=a.refresh,newer=b.refresh,alphas=19,repeats=3,exact_queue_parity=True))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/portal-topology-candidate-20261007')
out=dict(result='PASS',checks=checks,baseline_median_ms=statistics.median(timings[0]),candidate_median_ms=statistics.median(timings[1]),baseline_total_ms=sum(timings[0]),candidate_total_ms=sum(timings[1]),scope='15 captured intervals, exact portal queue parity including endpoints and bounded cache eviction; no fullscene/live performance claim')
(cp/'tests.json').write_text(json.dumps(out,indent=2));print({k:x for k,x in out.items() if k!='checks'})
