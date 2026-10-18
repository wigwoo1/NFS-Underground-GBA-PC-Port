"""Paired road asset reuse preserves original scratch results and rejects wrong owners."""
import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_planner import EndpointRoadPlanner
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
frames=r['wall_diagnostic_frames'];history=EndpointRoadPlanner(rom,table);count=0;rejected=0
try:
 history.plan(ClosedGraph.decode(Path(frames[0]['graph']).read_bytes()))
 for row in frames[1:]:
  scene=ClosedGraph.decode(Path(row['graph']).read_bytes());memory=ClosedSceneMemory(scene,history.rom);assets=(scene,history.rom,memory,road_candidates(scene,memory));branch=history.fork()
  try:
   for bad in ((object(),*assets[1:]),(scene,bytes(bytearray(rom)),*assets[2:])):
    try:branch.plan(scene,assets=bad)
    except ValueError as e:assert 'ownership mismatch' in str(e);rejected+=1
    else:raise AssertionError('Wrong assets accepted')
   reused=branch.plan(scene,assets=assets)
   assert reused==history.plan(scene);count+=1
  finally:branch.close()
finally:history.close()
print('PASS asset reuse:',count,'complete endpoint results exact;',rejected,'wrong owners rejected')
