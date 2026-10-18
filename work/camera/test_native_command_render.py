"""Native command asset packet 4K diagnostic replay comparison."""
from pathlib import Path
import os,subprocess,json,hashlib
from PIL import Image
p=Path('work/camera').resolve();f=p/'overflow-scene-171';cases=[]
reference=json.loads((p/'road-owned-bounds-render-tests.json').read_text())['cases']
for index,alpha in enumerate(('0.25','0.5','0.75')):
 raw=(f/f'native-command-owned-{alpha}.bin').read_bytes();second=bytearray(raw);second[16:32]=(f/'new.bin').read_bytes()[16:32]
 other=f/f'native-command-owned-{alpha}-next.bin';other.write_bytes(second)
 env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(f/'intentionally-missing-sidecar'),NF_PREVIEW_FRACTION=alpha,NF_PREVIEW_PHASE='2')
 subprocess.run([str(p/'sampled-road-clip-preview.exe'),str(f/f'native-command-owned-{alpha}.bin'),str(other),str(f/f'native-command-render-{alpha}')],check=True,capture_output=True,env=env)
 with Image.open(f/f'native-command-render-{alpha}-2.ppm') as im:
  assert im.size==(3840,2160);image=im.convert('RGB');digest=hashlib.sha256(image.tobytes()).hexdigest()
  image.resize((960,540)).save(f/f'native-command-render-{alpha}-review.png')
 expected=reference[index]['image_sha256'];cases.append(dict(alpha=float(alpha),image_sha256=digest,reference_image_sha256=expected,exact_render_parity=digest==expected))
report=dict(result='PASS' if all(c['exact_render_parity'] for c in cases) else 'DIFFERENT',cases=cases,scope='Offline complete native-command assets/lighting packet 4K replay against retained baseline; no live gameplay or timing proof.')
(p/'native-command-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
assert report['result']=='PASS'
