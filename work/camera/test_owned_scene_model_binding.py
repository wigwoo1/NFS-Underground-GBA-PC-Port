from pathlib import Path
import json
from owned_scene_bundle import SceneBundle
from owned_scene_model_binding import bind
p=Path('work/camera');poses=(p/'owned-object-poses.bin').read_bytes();textures=(p/'owned-object-textures.bin').read_bytes();checks=[];rejected=0
wrong_pose=bytearray(poses)
for offset in range(0,len(wrong_pose),292):wrong_pose[offset+44]^=1
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 bundle=SceneBundle.decode(file.read_bytes());plan=bind(bundle,poses,textures);assert len(plan)==1
 checks.append(dict(scene=file.name,objects=len(plan),texture_bytes=len(plan[0].texture)))
 for bad_pose,bad_texture in ((b'',textures),(poses,b''),(poses[:-1],textures),(poses,textures[:-1]),(bytes(wrong_pose),textures)):
  try:bind(bundle,bad_pose,bad_texture)
  except ValueError:rejected+=1
  else:raise AssertionError('Incomplete model binding accepted')
assert len(checks)==7 and rejected==35
r=dict(result='PASS_RAW_ID_DRAW_INPUT_SCENE_MODEL_BINDING',scenes=checks,invalid_payloads_rejected=rejected,scope='Immutable derived model draw payload; mesh attachment, complete pose closure and live GPU integration pending.')
(p/'owned-scene-model-binding.json').write_text(json.dumps(r,indent=2));print(r)
