import json,time,statistics,tracemalloc
from pathlib import Path
from dataclasses import replace
from owned_road_single_join_candidate import original,encode_road
from owned_closed_scene_memory import scene_memory
from owned_complete_road_candidates import road_candidates
ns={};exec(Path('work/camera/profile_complete_scene_unpack_candidate.py').read_text().split('for iteration in range(8):')[0],ns);scenes=ns['ns']['envs'][0]['scenes'];rom=ns['rom'];inputs=[]
for scene in scenes:
 for road in road_candidates(scene.graph,scene_memory(scene.graph,rom)):
  if not road.missing:inputs.append((scene.graph.graph.context,road,(0,239,0,159)))
assert inputs;expected=[original(*x) for x in inputs];cost={k:[] for k in ('baseline','candidate')}
for i in range(80):
 for label in (('baseline','candidate') if i%2==0 else ('candidate','baseline')):
  fn=original if label=='baseline' else encode_road;begin=time.perf_counter_ns();actual=[fn(*x) for x in inputs];cost[label].append((time.perf_counter_ns()-begin)/1e6);assert actual==expected
cases=[];ctx,road,bounds=inputs[0]
for b in ((0,0,0,0),(0.2,238.5,1.5,158.5),(0,240,0,159),(1,0,0,159),(0,239,0,float('nan')),(1,2,3)):
 cases.append((ctx,road,b))
for field,value in [('missing',('x',)),('vertices',road.vertices[:-1]),('offsets',b''),('face',b''),('material',b''),('animation',b''),('texture',b'')]:cases.append((ctx,replace(road,**{field:value}),bounds))
def result(fn,args):
 try:return ('ok',fn(*args))
 except Exception as e:return ('error',type(e).__name__,str(e))
for x in cases:assert result(original,x)==result(encode_road,x)
allocations=[]
for label in ('baseline','candidate','candidate','baseline'):
 fn=original if label=='baseline' else encode_road;tracemalloc.start();actual=[fn(*x) for x in inputs];current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();allocations.append(dict(label=label,current=current,peak=peak))
out=dict(result='PASS_SINGLE_JOIN_ROAD_RECORD',records=len(inputs),guards=len(cases),rounds=80,medians={k:statistics.median(v) for k,v in cost.items()},cost_ms=cost,allocations=allocations,scope='Actual complete captured road record bytes and original success/error parity. Isolated component; no complete preparation/native4K/live gain proof.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-single-join-20261010');cp.mkdir(exist_ok=True);(cp/'component.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='cost_ms'},indent=2))
