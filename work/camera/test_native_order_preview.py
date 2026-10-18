from pathlib import Path
import os,subprocess,json,struct,hashlib
from PIL import Image,ImageChops
from clip_metadata import validate
p=Path('work/camera').resolve();raw=(p/'clip-scene-141.bin').read_bytes();meta=json.loads((p/'clip-scene-141.json').read_text());validate(raw,meta['epoch'],meta)
env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(p/'captured-141.clips'),NF_PREVIEW_FRACTION='1',NF_PREVIEW_PHASE='2',NF_NATIVE_ORDER_FILE=str(p/'native-order-141.bin'))
def run(exe,label):
 return subprocess.run([str(p/exe),str(p/'clip-scene-140.bin'),str(p/'clip-scene-141.bin'),str(p/label)],env=env,capture_output=True)
assert run('captured-clip-preview.exe','native-order-baseline').returncode==0
assert run('native-order-preview.exe','native-order-render').returncode==0
assert subprocess.run([str(p/'captured-clip-preview.exe'),str(p/'owned-order-scene-140.bin'),str(p/'owned-order-scene-141.bin'),str(p/'owned-order-render')],env=env,capture_output=True).returncode==0
with Image.open(p/'native-order-baseline-2.ppm') as a,Image.open(p/'owned-order-render-2.ppm') as b:
 assert ImageChops.difference(a,b).getbbox() is None
with Image.open(p/'native-order-baseline-2.ppm') as a,Image.open(p/'native-order-render-2.ppm') as b:
 assert a.size==(3840,2160) and ImageChops.difference(a,b).getbbox() is None
data=(p/'native-order-141.bin').read_bytes();cases=[]
bad=bytearray(data);struct.pack_into('<I',bad,4,999);cases.append((bad,35))
bad=bytearray(data);bad[24:28]=bad[20:24];cases.append((bad,36))
cases.append((data+b'x',37))
for i,(bad,code) in enumerate(cases):
 path=p/'invalid-native-order.bin';path.write_bytes(bad);env['NF_NATIVE_ORDER_FILE']=str(path)
 assert run('native-order-preview.exe',f'invalid-order-{i}').returncode==code
report=dict(result='PASS',resolution=[3840,2160],changed_pixels=0,owned_packet_changed_pixels=0,invalid_cases=3,packet_sha256=hashlib.sha256(raw).hexdigest(),order_sha256=hashlib.sha256(data).hexdigest(),scope='Native ordered owned-packet and sidecar replay. Packet exported for offscreen test; no live scheduling or intermediate candidate insertion.')
(p/'native-order-preview-tests.json').write_text(json.dumps(report,indent=2));print(report)
