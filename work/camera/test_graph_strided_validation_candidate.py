import json,struct,time,statistics,textwrap
from pathlib import Path
from dataclasses import replace
from owned_graph_packet import GraphPacket
from owned_graph_strided_validation_candidate import original,parsed_graph,install,uninstall
setup=Path('work/camera/profile_complete_scene_unpack_candidate.py').read_text().split('for iteration in range(8):')[0]
ns={};exec(setup,ns);packets=ns['packets'];rom=ns['rom'];graphs=[s.graph.graph for s in ns['envs'][0]['scenes']] if 'envs' in ns else [s.graph.graph for s in ns['ns']['envs'][0]['scenes']]
def outcome(fn,g):
 try:
  mapping,required=fn(g);return ('ok',dict(mapping),required)
 except Exception as e:return ('error',type(e).__name__,str(e))
cases=[]
context=bytearray(896);struct.pack_into('<2H',context,92,10,150)
def geometry(n=1,index=0,material=65535,link=65535):
 desc=bytearray(48);struct.pack_into('<H',desc,2,n);struct.pack_into('<H',desc,4,65535);struct.pack_into('<H',desc,8,65535)
 ring=bytearray(n*68)
 for j in range(n):struct.pack_into('<H',ring,j*68+44,material);struct.pack_into('<H',ring,j*68+48,link)
 return struct.pack('<4I',index,n,0,0)+desc+ring
for n in range(1,33):
 g=GraphPacket(1,0,context,geometry(n,material=7),bytes(n*32),b'');cases.append(g)
 cases.extend([replace(g,root=1),replace(g,offsets=g.offsets[:-1]),replace(g,geometry=g.geometry[:-1]),replace(g,geometry=geometry(n,link=4)),replace(g,geometry=g.geometry+g.geometry)])
g=cases[0];cases.extend([replace(g,context=b''),replace(g,geometry=b'x'*63),replace(g,geometry=struct.pack('<4I',0,0,0,0)+bytes(48)),replace(g,geometry=struct.pack('<4I',0,33,0,0)+bytes(48+33*68)),replace(g,geometry=g.geometry[:18]+b'\x02\x00'+g.geometry[20:])])
for g in graphs+cases:assert outcome(original.func,g)==outcome(parsed_graph,g)
from owned_scene_process_transport import unpack,pack
cost={'baseline':[],'candidate':[]}
for iteration in range(30):
 for label in (('baseline','candidate') if iteration%2==0 else ('candidate','baseline')):
  (install if label=='candidate' else uninstall)();begin=time.perf_counter_ns();decoded=[unpack(p,rom) for p in packets];elapsed=time.perf_counter_ns()-begin
  assert [pack(f,s) for f,s in decoded]==packets;cost[label].append(elapsed/1e6)
uninstall()
out=dict(result='PASS_STRIDED_GRAPH_VALIDATION_AND_COMPLETE_UNPACK',guard_cases=len(cases),captured_graphs=len(graphs),rounds=30,medians={k:statistics.median(v) for k,v in cost.items()},cost_ms=cost,scope='Complete current captured endpoint decode/re-encode equality plus original/candidate parser success/error parity. Isolated optin, no native4K or live cadence qualification.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graph-strided-validation-20261010');cp.mkdir(exist_ok=True);(cp/'component.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='cost_ms'},indent=2))
