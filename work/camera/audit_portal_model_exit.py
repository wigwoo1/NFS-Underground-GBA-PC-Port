"""Identify an allocated scenery source leaving recovered portal coverage."""
import runpy,struct,json
from pathlib import Path
from owned_scene_bundle import chunks
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import SceneryProjection
v=runpy.run_path('work/camera/audit_complete_model_transition.py');folder=v['folder'];index=35
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
parents=[];evidence=[]
for endpoint,scene in enumerate(v['scenes']):
 state=scene.graph.context[:256];base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
 raw=v['sources'][endpoint].sources[base+index*164]
 chain=[]
 for h,data in chunks(scene.objects,'graph_objects'):
  for position in range(h[5]):
   if struct.unpack_from('<I',data,128+position*168)[0]==index:
    source=data[132+position*168:296+position*168]
    assert source==raw
    chain.append((h[3],position))
 assert len(chain)==1 and raw[136]!=255
 parent=chain[0][0];parents.append(parent)
 assert v['eligibility'](raw)=='project' and v['depth_distance'](raw,scene.graph.context[256:304])[0]>0
 builders=OwnedModelBuilders((folder/(('older','newer')[endpoint]+'.builders.bin')).read_bytes())
 builder=builders.at(base+index*164,matrix_base+raw[136]*48,scene.refresh)
 assert struct.unpack_from('<h',builder.source,54)[0]==32
 matrix=SceneryProjection(rom).matrix(builder.camera,builder.source,builder.initial_matrix)
 evidence.append(dict(endpoint=endpoint,parent=parent,position=chain[0][1],slot=raw[136],builder_refresh=builder.refresh,matrix=struct.unpack('<12i',matrix),portal=[q for q in v['portal'].sample(endpoint) if q[0]==parent]))
assert parents==[30,30] and evidence[0]['portal'] and not evidence[1]['portal']
samples=[]
for i in range(101):
 queue=v['portal'].sample(i/100)
 samples.append(dict(alpha=i/100,regions=[q for q in queue if q[0]==30 and not q[5]&0x88 and q[1]<=q[2] and q[3]<=q[4]]))
report=dict(source=index,model=32,classification='allocated positive-depth source exits portal coverage',endpoints=evidence,samples=samples)
(folder/'portal-model-exit.json').write_text(json.dumps(report,indent=2))
print('PASS allocated source/chain/builder closure: portal30 exit, not depth exit/removal')
print('visible sampled alphas',[s['alpha'] for s in samples if s['regions']])
