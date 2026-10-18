from pathlib import Path
import os,subprocess,struct,json,hashlib
from PIL import Image
p=Path('work/camera').resolve();raw=(p/'paired-scene-160-0.5.bin').read_bytes();other=bytearray(raw);other[16:32]=(p/'paired-scene-160-1.0.bin').read_bytes()[16:32];next_path=p/'paired-scene-160-midpoint-next.bin';next_path.write_bytes(other)
env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(p/'intentionally-missing-sidecar'),NF_PREVIEW_FRACTION='0.5',NF_PREVIEW_PHASE='2')
r=subprocess.run([str(p/'sampled-road-clip-preview.exe'),str(p/'paired-scene-160-0.5.bin'),str(next_path),str(p/'paired-scene-160-render')],env=env,capture_output=True,text=True);print('renderer',r.returncode,r.stdout[-1000:],r.stderr[-1000:]);r.check_returncode()
with Image.open(p/'paired-scene-160-render-2.ppm') as im:
 assert im.size==(3840,2160);rgb=im.convert('RGB');digest=hashlib.sha256(rgb.tobytes()).hexdigest();rgb.resize((960,540)).save(p/'paired-scene-160-render-review.png')
report=dict(result='PASS',dimensions=[3840,2160],pair_newer_serial=160,alpha=.5,image_sha256=digest,scope='Offscreen renderer consumes generated paired midpoint packet, owned bounds and lighting. Duplicate midpoint pose with newer endpoint header isolates this sample; no additional pose interpolation. Not live motion/timing verification.')
(p/'paired-scene-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
