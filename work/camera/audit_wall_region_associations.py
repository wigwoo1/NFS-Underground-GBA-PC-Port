import sys,json,struct
from pathlib import Path
sys.path.insert(0,'work/camera');s={};exec(Path('work/camera/test_source_transition_adapter.py').read_text().split('table=struct.unpack',1)[0],s)
from owned_scene_bundle import chunks
from owned_wall_region_candidates import regions
reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);result=[]
for label,scene in zip(('older','newer'),s['scenes']):
 closed=scene.graph;recovered=[list(r) for r in regions(closed.graph,reciprocal)];actual=[dict(header=list(h),region=list(struct.unpack('<8H',raw[32:48]))) for h,raw in chunks(closed.associations,'associations')]
 result.append(dict(endpoint=label,recovered=recovered,associations=actual))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-region-associations-20261007');cp.mkdir(exist_ok=True);(cp/'regions.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
