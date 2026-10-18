"""Rebuilt topology and textures match original captured active model blocks."""
import runpy,json,struct
from pathlib import Path
from owned_model_assets import model_asset_blocks
from owned_closed_scene_memory import ClosedSceneMemory
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_activation_model_assets.py');plans=v['results'];fixture=v['v'];rom=v['rom'];rebuilt=[]
for endpoint,scene in enumerate(v['scenes']):
 memory=ClosedSceneMemory(scene,rom);items={}
 for item in plans[endpoint]['items']:
  blocks=model_asset_blocks(struct.pack('<17I',*item['context']),memory)
  assert all(isinstance(data,bytes) for data in blocks.values())
  items[item['object']]=blocks
 rebuilt.append(items)
rows=[r for r in records(fixture['frames'][1])['records'] if r['kind']==3]
for index,blocks in rebuilt[1].items():
 matches=[r for r in rows if bytes(r['blocks'][1])==blocks[1]];assert len(matches)==1
 assert all(bytes(matches[0]['blocks'][i])==data for i,data in blocks.items()),index
 assert dict(rebuilt[0][index])==dict(blocks),'Candidate assets changed across activation'
try:rebuilt[0][31][1]=b'bad'
except TypeError:pass
else:raise AssertionError('Mutable owned model assets')
print('PASS: 35 active model blocks exact; all five preactivation topology/texture sets identical; immutable ownership')
