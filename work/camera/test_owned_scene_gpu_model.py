from pathlib import Path
import json
from owned_scene_bundle import SceneBundle
from owned_scene_model_binding import attach_meshes
from owned_scene_gpu_model import blocks,encode,palette
from owned_motion_pairs import records
p=Path('work/camera');references=[]
for file in (p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'):
 for row in records(file.read_bytes())['records']:
  if row['kind']==3:references.append(row['blocks'])
checks=[]
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 bundle=SceneBundle.decode(file.read_bytes());draw=attach_meshes(bundle,(p/'owned-object-poses.bin').read_bytes(),(p/'owned-object-textures.bin').read_bytes(),{(7,0):(p/'model-assets/7-0.nma').read_bytes()})[0]
 matches=[b for b in references if bytes(b[2])==draw.draw.matrix];assert len(matches)==1
 original=matches[0];owned_palette=palette(bundle,draw,(p/'owned-object-palettes.bin').read_bytes());owned=blocks(bundle,draw,owned_palette)
 matches=[b for b in references if bytes(b[2])==owned[2]];assert len(matches)==1
 original=matches[0]
 for i in range(1,11):assert owned[i]==bytes(original[i]),(file.name,i)
 assert owned[11][2:]==bytes(original[11][2:]),(file.name,'visible palette')
 assert owned[0][56:60]==bytes(original[0][56:60]) and owned[0][64:68]==bytes(original[0][64:68])
 assert len(encode(bundle,draw,owned_palette))>51200
 checks.append(file.name)
r=dict(result='PASS_SCENE_GPU_MODEL_BLOCK_PARITY',scenes_exact=checks,complete_blocks_exact=10,visible_palette_entries_exact=255,context_consumed_fields_exact=True,scope='GPU input adapter parity; Palette entries1..255 independently exact; entry0 background differs; model zero writes display-row background. Actual GPU replay/live publication pending.')
(p/'owned-scene-gpu-model.json').write_text(json.dumps(r,indent=2));print(r)


