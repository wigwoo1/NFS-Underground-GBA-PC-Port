import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
import owned_motion_visibility as visibility
from owned_portal_traversal import traverse as baseline
from owned_portal_traversal_point_local_candidate import traverse as candidate
from owned_portal_point_cache_candidate import traverse as existing
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[];times=[[],[],[]]
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  graphs=[ClosedGraph.decode(Path(f['graph']).read_bytes()).graph for f in (fa,fb)];frames=[Path(f['regenerated']).read_bytes() for f in (fa,fb)]
  portals=[PortalMotionPair(*graphs,table,PreparedMotionPair(*frames)) for _ in range(3)]
  for alpha in [i/20 for i in range(21)]:
   outputs=[]
   for which,fn in enumerate((baseline,existing,candidate)):
    visibility.traverse=fn;begin=time.perf_counter_ns();outputs.append(portals[which].sample(alpha));times[which].append(time.perf_counter_ns()-begin)
   assert outputs[0]==outputs[1]==outputs[2],(graphs[0].refresh,alpha)
   checks.append(dict(refresh=graphs[0].refresh,alpha=alpha,regions=len(outputs[0])))
finally:visibility.traverse=baseline
out=dict(result='PASS_LOCAL_PORTAL_POINT_PARITY',samples=len(checks),checks=checks,baseline_median_ns=statistics.median(times[0]),existing_candidate_median_ns=statistics.median(times[1]),candidate_median_ns=statistics.median(times[2]),scope='15 captured source pairs, 21 alphas each, exact portal queues including bounds/flags/order. Per-traversal coordinate memo only; sequential timing, not live cadence qualification.')
Path('work/camera/prototype-runs/portal-point-local-parity.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
