"""Activation candidate enumeration retains original active-only dispatch default."""
from pathlib import Path
import json,struct
from owned_graph_packet import GraphPacket
from owned_closed_graph import ClosedGraph
from owned_scene_bundle import chunks
from owned_ordinary_model_visits import ordinary_model_visits
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791280093968732600.json').read_text());folder=Path(r['full_scene_failure_capture']['folder']);scenes=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame)
 scenes.append(ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*((folder/(label+'.'+f+'.bin')).read_bytes() for f in ('objects','callbacks','associations'))))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));results=[]
for i,scene in enumerate(scenes):
 queue=portal.sample(i);ordinary=ordinary_model_visits(scene,queue);candidates=ordinary_model_visits(scene,queue,True)
 assert all(v['allocated'] for v in ordinary)
 assert {v['object'] for v in ordinary}=={v['object'] for v in candidates if v['allocated']}
 assert all(v['source'][136]==255 for v in candidates if not v['allocated'])
 results.append(dict(endpoint=i,active=[v['object'] for v in ordinary],candidates=[v['object'] for v in candidates]))
print(results)
assert set(results[1]['active'])-set(results[0]['active'])=={31,34,37,44,48}
assert {31,34,37,44,48}<=set(results[0]['candidates'])
print('PASS: all five activating models have owned candidate visits at both endpoints')

from owned_motion_scene import MotionScene
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_candidates import scenery_candidates
poses=[]
for i,label in enumerate(('older','newer')):
 supplements=ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scenes[i])
 scene=MotionScene(scenes[i],supplements,OwnedModelBuilders((folder/(label+'.builders.bin')).read_bytes()))
 rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
 candidates=scenery_candidates(scene,portal.sample(i),frames[i],rom)
 assert len(candidates)==5 and all(len(c.matrix)==48 for c in candidates)
 assert all(c.allocated==bool(i) for c in candidates)
 poses.append(candidates)
assert {c.object_index for c in poses[0]}=={c.object_index for c in poses[1]}
assert all(c.builder_refresh is None for c in poses[0])
print('PASS: five inactive candidate poses, five exact consumed active poses; allocation preserved')
