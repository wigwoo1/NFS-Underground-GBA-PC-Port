import sys,json,dataclasses,hashlib,tracemalloc
from pathlib import Path
from types import SimpleNamespace
from owned_graph_packet import GraphPacket
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
p=Path('work/camera');original={};exec((p/'owned_complete_road_candidates.before-texture-view.py').read_text(),original)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();checks=[]
for refresh in (8754,8758,8762,8765,8769,8772,8776):
 g=GraphPacket.decode((p/f'graph-packets/{refresh}.ngp').read_bytes());closed=SimpleNamespace(graph=g);memory=ClosedSceneMemory(closed,rom)
 peaks=[];results=[]
 for fn in (original['road_candidates'],road_candidates):
  tracemalloc.start();tracemalloc.reset_peak();out=fn(closed,memory);peaks.append(tracemalloc.get_traced_memory()[1]);tracemalloc.stop();results.append(out)
 a,b=results;assert len(a)==len(b)
 for x,y in zip(a,b):
  assert dataclasses.asdict(x)==dataclasses.asdict(y)
  assert y.texture is None or isinstance(y.texture,bytes)
 checks.append(dict(refresh=refresh,roads=len(b),baseline_peak_bytes=peaks[0],view_peak_bytes=peaks[1]))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-material-texture-view-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Seven captured graph road closures field-by-field exact; all returned textures remain immutable bytes. Tracemalloc isolated allocation evidence, not live timing or full-port fidelity.'),indent=2))
for name in ('test_road_material_texture_view.py','owned_complete_road_candidates.py','owned_complete_road_candidates.before-texture-view.py'):(cp/name).write_bytes((p/name).read_bytes())
print(json.dumps(checks))
