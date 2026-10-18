import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');ns={};exec((p/'test_sky_continuous_gpu_readback.py').read_text().split('from owned_sky_sampler import SkyAsset')[0],ns)
expected={};checks=[]
for name in ('owned-sky-spatial-batch.dll','owned-sky-spatial-runs.dll'):
 d=C.CDLL(str((p/name).resolve()));f=d.nf_owned_gpu_render_sky;f.argtypes=ns['api'].argtypes
 try:
  for weight in (0,.2,.4,.6,.8,.99):
   assert f(ns['frame'],len(ns['raw']),ns['a'],ns['b'],15136,weight,ns['out'],len(ns['out']))==0
   digest=hashlib.sha256(ns['out'].raw).hexdigest()
   if weight in expected:assert digest==expected[weight],(weight,'Merged geometry pixel mismatch')
   else:expected[weight]=digest
   checks.append(dict(renderer=name,weight=weight,rgb_sha256=digest))
 finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-spatial-runs-fullpixel-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,pixels_per_phase=8294400,scope='Six fractional background phases, full4K RGB exact merged vs unmerged sky geometry; not fullscene composition/live timing/scanout.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print('PASS merged/unmerged six-phase full4K pixels exact')
