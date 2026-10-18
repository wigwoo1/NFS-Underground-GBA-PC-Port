"""Check fractional sky pixels using the DLL selected by the playable launcher."""
import ctypes as C, json, hashlib
from pathlib import Path
p=Path('work/camera'); ns={}
exec((p/'test_sky_continuous_gpu_readback.py').read_text().split('from owned_sky_sampler import SkyAsset')[0],ns)
d=C.CDLL(str((p/'owned-sky-source-context-candidate.dll').resolve()))
f=d.nf_owned_gpu_render_sky; f.argtypes=ns['api'].argtypes
checks=[]; previous=None
try:
 for weight in (0,.2,.4,.6,.8,.99):
  assert f(ns['frame'],len(ns['raw']),ns['a'],ns['b'],15136,weight,ns['out'],len(ns['out']))==0
  pixels=ns['out'].raw
  reference=ns['sky_rgba'](ns['SkySamples'](ns['lower'],ns['upper'],weight,0x06000000+10560),ns['palettes'])
  centers=bytearray(); maximum=0
  for i in range(15136):
   y,x=divmod(10560+i,240)
   at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3
   color=pixels[at:at+3]; centers.extend(color)
   maximum=max(maximum,max(abs(a-b) for a,b in zip(color,reference[i*4:i*4+3])))
  assert maximum<=1,(weight,maximum)
  changed=None if previous is None else sum(centers[i:i+3]!=previous[i:i+3] for i in range(0,len(centers),3))
  if previous is not None: assert changed>0,(weight,'Frozen fractional pixels')
  checks.append(dict(weight=weight,changed_centers=changed,max_channel_error=maximum,rgb_sha256=hashlib.sha256(pixels).hexdigest()))
  previous=centers
finally: assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/launcher-sky-pixels-20261008'); cp.mkdir(exist_ok=True)
result=dict(result='PASS',renderer='owned-sky-source-context-candidate.dll',renderer_sha256=hashlib.sha256((p/'owned-sky-source-context-candidate.dll').read_bytes()).hexdigest(),checks=checks,scope='Actual launcher DLL background-only 4K GPU output; fixed integer texture with fractional weights. Palette blend oracle at15136 centers. No full-scene, live cadence or scanout certification.')
(cp/'result.json').write_text(json.dumps(result,indent=2)); (cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes()); print(json.dumps(result,indent=2))

