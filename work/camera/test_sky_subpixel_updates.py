"""Verify actual 4K sky pixels change within one source-pixel interval."""
import runpy, json, ctypes as C
from pathlib import Path
ns=runpy.run_path('work/camera/test_sky_continuous_gpu_readback.py')
d=ns['d']; api=ns['api']; frame=ns['frame']; raw=ns['raw']; out=ns['out']
sample=ns['samples']; palettes=ns['palettes']; SkySamples=ns['SkySamples']; reference_rgba=ns['sky_rgba']
a=C.create_string_buffer(sample.lower); b=C.create_string_buffer(sample.upper)
checks=[]; previous=None
try:
 for weight in (.2,.4,.6,.8):
  assert api(frame,len(raw),a,b,15136,weight,out,len(out))==0
  reference=reference_rgba(SkySamples(sample.lower,sample.upper,weight,sample.destination),palettes)
  pixels=out.raw; centers=bytearray(); maximum=0
  for i in range(15136):
   y,x=divmod(10560+i,240); at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3
   color=pixels[at:at+3]; centers.extend(color)
   error=max(abs(v-w) for v,w in zip(color,reference[i*4:i*4+3])); maximum=max(maximum,error)
   assert error<=1,(weight,i,error)
  changed=None if previous is None else sum(centers[i:i+3]!=previous[i:i+3] for i in range(0,len(centers),3))
  if previous is not None: assert changed>0,'Fractional sky change produced identical pixels'
  checks.append(dict(weight=weight,changed_sky_centers=changed,max_channel_error=maximum)); previous=centers
finally: assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-subpixel-updates-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual 4K background GPU output, fixed integer source pixels with varying fractional weights; not physical scanout or sustained gameplay cadence'),indent=2))
(cp/'test_sky_subpixel_updates.py').write_text(Path(__file__).read_text())
print(json.dumps(checks)); print('PASS actual 4K fractional sky updates')
