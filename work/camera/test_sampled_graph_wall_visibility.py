import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_sampled_graph_wall_visibility import selected_graph_walls
from owned_wall_projection import projected
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[]
for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(fa['graph']).read_bytes()).graph;b=ClosedGraph.decode(Path(fb['graph']).read_bytes()).graph;motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());portal=PortalMotionPair(a,b,table,motion);samples=[]
 for alpha in (0,.25,.5,.75,1):
  selected=selected_graph_walls(portal,alpha)
  if alpha in (0,1):
   exact,_=projected(b if alpha==1 else a,table);exact=sorted(exact,key=lambda row:(-row[0],row[2].edge))
   assert [(c.ordinal,c.descriptor,c.edge,c.wall.vertices) for c,v in selected]==[(o,q[0],w.edge,w.vertices) for o,q,w,scratch in exact]
   for (c,v),(o,q,w,scratch) in zip(selected,exact):assert v.x==struct.unpack_from('<2h',scratch) and v.y==struct.unpack_from('<4h',scratch,8) and v.flags==struct.unpack_from('<H',scratch,48)[0]
  samples.append(dict(alpha=alpha,visible_walls=len(selected),offset_walls=sum(any(c.wall.offsets) for c,v in selected)))
 checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
out=dict(result='PASS_SAMPLED_GRAPH_WALL_VISIBILITY',intervals=len(checks),checks=checks,scope='Complete main graph wall selection with stable raw vertex offsets; endpoint ordering/projection exact. GPU insertion and moving offset interpolation pending.')
Path('work/camera/sampled-graph-wall-visibility-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))
