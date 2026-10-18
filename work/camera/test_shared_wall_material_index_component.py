import os,json,time,statistics
from pathlib import Path
from types import SimpleNamespace
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'actual-material-index-setup','exec'))
import owned_shared_wall_material_index_candidate as reuse
original=(reuse.original_metadata,reuse.original_sources);candidate=(reuse.wall_metadata,reuse.wall_sources);times={False:[],True:[]}
for iteration in range(30):
 for selected in ((False,True) if iteration%2==0 else (True,False)):
  reuse.clear();outputs=[];started=time.perf_counter_ns();meta,source=candidate if selected else original
  for scene in scenes:
   graph=scene.graph.graph;portal=SimpleNamespace();m=meta(portal,graph);walls=source(graph,validated=True,descriptors={23,25,26,28,29,31,32},material_cache=[graph,None]);outputs.append((m,walls))
  times[selected].append((time.perf_counter_ns()-started)/1e6)
  if selected:assert outputs==reference
  else:reference=outputs
assert reuse.stats['hits']>0 and reuse.stats['misses']>0
out=dict(result='PASS_SHARED_WALL_MATERIAL_INDEX_COMPONENT',iterations=30,selection_stats=dict(reuse.stats),baseline_median_ms=statistics.median(times[False]),candidate_median_ms=statistics.median(times[True]),scope='Real graph metadata and selected descriptor complete WallSource equality; cold shared index each comparison, not complete preparation/live/4K qualification.')
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-wall-material-index-20261010');folder.mkdir(exist_ok=True);(folder/'component.json').write_text(json.dumps(out,indent=2));print(out)
