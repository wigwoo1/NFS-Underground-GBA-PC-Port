import json,struct,sys,time,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
import owned_motion_wall_regions as regions
from owned_graph_wall_sources import wall_sources as baseline
from owned_graph_wall_sources_index_candidate import wall_sources as candidate
from owned_sampled_graph_wall_visibility import selected_graph_walls
from owned_sampled_graph_gpu import sampled_graph_gpu_records
raw=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[];times=[[],[]]
def fingerprint(rows):
 return [(vars(c)|{'wall':vars(c.wall)},vars(v)) for c,v in rows]
for fa,fb in zip(raw['wall_diagnostic_frames'],raw['wall_diagnostic_frames'][1:]):
 graphs=[ClosedGraph.decode(Path(f['graph']).read_bytes()).graph for f in (fa,fb)]
 frames=[Path(f['regenerated']).read_bytes() for f in (fa,fb)]
 portals=[PortalMotionPair(*graphs,table,PreparedMotionPair(*frames)) for _ in range(2)]
 for alpha in (0,.125,.25,.375,.5,.625,.75,.875,1):
  outputs=[];gpu=[]
  for i,fn in enumerate((baseline,candidate)):
   regions.wall_sources=fn;begin=time.perf_counter_ns();outputs.append(fingerprint(selected_graph_walls(portals[i],alpha)));times[i].append(time.perf_counter_ns()-begin)
   gpu.append(sampled_graph_gpu_records(portals[i],alpha))
  assert outputs[0]==outputs[1],('visibility',graphs[0].refresh,alpha)
  assert gpu[0]==gpu[1],('GPU records',graphs[0].refresh,alpha)
  checks.append(dict(older=graphs[0].refresh,newer=graphs[1].refresh,alpha=alpha,walls=len(outputs[0]),gpu_records=len(gpu[0])))
regions.wall_sources=baseline
out=dict(result='PASS_COMPLETE_SAMPLED_WALL_INDEX_PARITY',samples=len(checks),pairs=len(portals) if False else len(raw['wall_diagnostic_frames'])-1,checks=checks,baseline_selection_median_ns=statistics.median(times[0]),candidate_selection_median_ns=statistics.median(times[1]),scope='Exact complete sampled wall visibility, projection flags, bounds, source bytes and encoded GPU draw ordering on captured pairs; not broad fidelity or live cadence qualification.')
Path('work/camera/prototype-runs/wall-source-index-visibility.json').write_text(json.dumps(out,indent=2));print(out['result'],out['samples'],out['baseline_selection_median_ns'],out['candidate_selection_median_ns'])
