import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph_validation_views_candidate import validation_chunks,original_chunks,install,uninstall
setup=Path('work/camera/profile_complete_scene_unpack_candidate.py').read_text().split('for iteration in range(8):')[0];ns={};exec(setup,ns);packets=ns['packets'];rom=ns['rom']
def result(fn,raw,kind):
 try:return ('ok',[(h,bytes(d)) for h,d in fn(raw,kind)])
 except Exception as e:return ('error',type(e).__name__,str(e))
cases=[]
for kind,size,index in [('graph_objects',296,6),('associations',400,None),('objects',248,6),('callbacks',244,None),('supplements',100,5),('textures',130,None)]:
 raw=bytearray(size)
 if index is not None:struct.pack_into('<I',raw,index*4,size-(128 if kind=='graph_objects' else 80 if kind=='objects' else 32))
 if kind=='textures':struct.pack_into('<I',raw,40,10)
 raw=bytes(raw)
 for cut in (0,1,31,32,size-1,size):cases.append((raw[:cut],kind))
 cases.append((raw+raw,kind));cases.append((bytearray(raw),kind))
for raw,kind in cases:assert result(original_chunks,raw,kind)==result(validation_chunks,raw,kind)
from owned_scene_process_transport import unpack,pack
cost={'baseline':[],'candidate':[]}
for i in range(40):
 for label in (('baseline','candidate') if i%2==0 else ('candidate','baseline')):
  (install if label=='candidate' else uninstall)();begin=time.perf_counter_ns();decoded=[unpack(p,rom) for p in packets];cost[label].append((time.perf_counter_ns()-begin)/1e6)
  assert [pack(f,s) for f,s in decoded]==packets
  for f,s in decoded:
   assert all(type(x) is bytes for x in (f,s.graph.objects,s.graph.callbacks,s.graph.associations,s.graph.graph.context,s.graph.graph.geometry,s.graph.graph.offsets,s.graph.graph.materials))
uninstall();out=dict(result='PASS_PRIVATE_GRAPH_VALIDATION_VIEWS',guards=len(cases),rounds=40,medians={k:statistics.median(v) for k,v in cost.items()},cost_ms=cost,scope='Complete captured endpoint decode/reencoding and published immutable bytes parity; section views reference private bytes only, no shared memory. Isolated, no live/native4K claim.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graph-validation-views-20261010');cp.mkdir(exist_ok=True);(cp/'component.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='cost_ms'},indent=2))
