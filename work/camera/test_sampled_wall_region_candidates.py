"""Real paired-scene wall candidate coverage and continuous clip component test."""
from pathlib import Path
import json,struct
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_motion_wall_regions import wall_region_candidates
from owned_graph_wall_sources import wall_sources
from owned_wall_region_candidates import regions,hidden
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[];fractional=0
for old,new in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(old['graph']).read_bytes()).graph;b=ClosedGraph.decode(Path(new['graph']).read_bytes()).graph;motion=PreparedMotionPair(Path(old['regenerated']).read_bytes(),Path(new['regenerated']).read_bytes());pair=PortalMotionPair(a,b,table,motion);samples=[]
 for alpha in (0,.001,.25,.5,.75,.999,1):
  candidates=wall_region_candidates(pair,alpha);g=b if alpha==1 else a;all_sources={(w.descriptor,w.edge):w for w in wall_sources(g)}
  for c in candidates:
   assert c.wall==all_sources[(c.descriptor,c.edge)] and not hidden(c.wall) and not c.region_flags&8
   assert len(c.wall.vertices)==136 and len(c.wall.offsets)==64 and len(c.wall.animation)==8
   assert len(c.wall.texture)==(1<<c.wall.shift)*c.wall.height
   assert c.bounds[0]<=c.bounds[1] and c.bounds[2]<=c.bounds[3]
   fractional+=any(abs(x-round(x))>1e-6 for x in c.bounds)
  if alpha in (0,1):
   expected=[(ordinal,q[0],w.edge,tuple(float(x) for x in q[1:5])) for ordinal,q in enumerate(regions(g,table)) if not q[5]&8 and q[1]<=q[2] and q[3]<=q[4] for w in all_sources.values() if w.descriptor==q[0] and not hidden(w)]
   assert [(c.ordinal,c.descriptor,c.edge,c.bounds) for c in candidates]==expected
  samples.append(dict(alpha=alpha,candidates=len(candidates),descriptors=sorted(set(c.descriptor for c in candidates))))
 checks.append(dict(older=old['refresh'],newer=new['refresh'],samples=samples))
assert fractional
out=dict(result='PASS_COMPLETE_SAMPLED_WALL_REGION_CANDIDATES',intervals=len(checks),fractional_clip_candidates=fractional,checks=checks,scope='Raw wall sources with sampled portal clip bounds; candidate list still needs surface visibility/near clipping/deferred ordering. No GPU/live motion completion claim.')
Path('work/camera/sampled-wall-region-candidates-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks),fractional)
