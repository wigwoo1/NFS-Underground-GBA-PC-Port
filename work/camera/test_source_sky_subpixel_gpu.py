"""Current source renderer sky pixel movement below one source texel."""
import ctypes as C,json
from pathlib import Path
base=Path('work/camera/test_sky_continuous_gpu_readback.py').read_text()
base=base.replace("owned-sky-gpu.dll","owned-sky-source-context-candidate.dll").replace('sky-continuous-gpu-readback-20261006','source-sky-subpixel-gpu-20261007')
ns={};exec(compile(base,'current_source_sky_setup','exec'),ns)
d=ns['d'];api=ns['api'];sample=ns['samples'];a=C.create_string_buffer(sample.lower);b=C.create_string_buffer(sample.upper)
checks=[];previous=None
assert d.nf_owned_gpu_window(0)==0
try:
 for weight in (0,.01,.02,.1,.2,.4,.6,.8,.99):
  rc=api(ns['frame'],len(ns['raw']),a,b,15136,weight,ns['out'],len(ns['out']));assert rc==0,(weight,rc)
  pixels=ns['out'].raw;reference=ns['sky_rgba'](ns['SkySamples'](sample.lower,sample.upper,weight,sample.destination),ns['palettes'])
  centers=bytearray();maximum=0
  for i in range(15136):
   y,x=divmod(10560+i,240);at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3
   color=pixels[at:at+3];centers.extend(color)
   error=max(abs(v-w) for v,w in zip(color,reference[i*4:i*4+3]));maximum=max(maximum,error)
   assert error<=1,(weight,i,error)
  changed=None if previous is None else sum(centers[i:i+3]!=previous[i:i+3] for i in range(0,len(centers),3))
  if previous is not None:assert changed>0,(weight,'Held sky pixels')
  checks.append(dict(weight=weight,changed_centers=changed,max_channel_error=maximum));previous=centers
finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-sky-subpixel-gpu-20261007')
(cp/'subpixel.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Current source DLL actual 4K GPU readback against palette blend reference; fixed diagnostic background, not live cadence or physical scanout'),indent=2))
(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps(checks))



