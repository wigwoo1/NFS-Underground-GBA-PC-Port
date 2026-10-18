from pathlib import Path
import struct,json
from owned_model_mesh import ModelMesh
from owned_scene_bundle import SceneBundle
from owned_scene_model_binding import bind,attach_meshes
from owned_motion_pairs import records
p=Path('work/camera');mesh=ModelMesh.decode((p/'model-assets/7-0.nma').read_bytes());references=[]
for file in (p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'):
 frame=records(file.read_bytes())
 for row in frame['records']:
  if row['kind']==3:references.append(row['blocks'])
checks=[]
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 bundle=SceneBundle.decode(file.read_bytes())
 assert len(attach_meshes(bundle,(p/'owned-object-poses.bin').read_bytes(),(p/'owned-object-textures.bin').read_bytes(),{(7,0):(p/'model-assets/7-0.nma').read_bytes()}))==1
 draw=bind(bundle,(p/'owned-object-poses.bin').read_bytes(),(p/'owned-object-textures.bin').read_bytes())[0]
 matches=[b for b in references if bytes(b[2])==draw.matrix and bytes(b[10])==draw.texture];assert len(matches)==1
 b=matches[0]
 assert all(mesh.blocks[i]==bytes(b[j]) for i,j in ((0,1),(1,4),(2,5),(3,6),(4,7),(5,8)))
 checks.append(file.name)
rejected=0
for file in (p/'model-assets').glob('*.nma'):
 raw=file.read_bytes();ModelMesh.decode(raw)
 for bad in (raw[:-1],raw[:60],bytes([raw[0]^1])+raw[1:]):
  try:ModelMesh.decode(bad)
  except ValueError:rejected+=1
  else:raise AssertionError('Bad mesh accepted')
assert len(checks)==7 and rejected==18
r=dict(result='PASS_SCENE_MODEL_MESH_DRAW_PARITY',scenes_exact=checks,mesh_blocks_exact=6,invalid_meshes_rejected=rejected,scope='Independent full model mesh block parity; unified transport and live rendering pending.')
(p/'owned-scene-model-mesh.json').write_text(json.dumps(r,indent=2));print(r)
