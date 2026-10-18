"""Trace actual extra wall source candidates, visibility and portal bounds."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'work/camera');scope={};exec(Path('work/camera/test_source_transition_adapter.py').read_text().split('try:',1)[0],scope)
import owned_wall_visibility_candidate as v
from owned_sampled_graph_wall_visibility import selected_graph_walls
original=v.batch;captured=[]
def track(calls):
 outputs=original(calls)
 for c,o in zip(calls,outputs):
  wall,desc,edge,fb,bounds,base,table=c
  ref=v.select_wall(*c)
  captured.append(dict(source=hashlib.sha256(wall.vertices).hexdigest(),descriptor=wall.descriptor,edge_index=wall.edge,camera_edge=list(edge),bounds=list(bounds),visible=o.visible,reason=o.reason,x=list(o.x),y=list(o.y),reference_visible=ref.visible,reference_reason=ref.reason))
 return outputs
v.batch=track;pair=scope['prepared'];portal=pair.pair.portal;checks=[]
try:
 for alpha in (0,1e-9,.0001,.01,.1,1):
  captured.clear();frame,*_=pair.sample(alpha);walls=[r for r in scope['records'](frame)['records'] if r['kind']==2];checks.append(dict(alpha=alpha,selected=len(walls),visible_sources=[hashlib.sha256(r['blocks'][0]).hexdigest() for r in walls],calls=list(captured)))
finally:v.batch=original;pair.close();scope['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-membership-full-scene-trace-20261007');cp.mkdir(exist_ok=True)
(cp/'trace.json').write_text(json.dumps(checks,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
a=set(checks[0]['visible_sources']);b={c['source']:c for c in checks[1]['calls'] if c['visible']}
extra=[c for k,c in b.items() if k not in a]
summary=dict(counts=[dict(alpha=c['alpha'],selected=c['selected'],native_reference_disagreements=sum(x['visible']!=x['reference_visible'] for x in c['calls'])) for c in checks],extra=extra)
(cp/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
