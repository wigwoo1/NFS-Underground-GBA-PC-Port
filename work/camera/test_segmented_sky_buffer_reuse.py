"""Full4K sky parity plus bounded native buffer reuse/close verification."""
import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');ns={};exec((p/'test_sky_continuous_gpu_readback.py').read_text().split('from owned_sky_sampler import SkyAsset')[0],ns)
expected={};checks=[];stats=[]
for name in ('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-sky-buffer-candidate.dll'):
 d=C.CDLL(str((p/name).resolve()));f=d.nf_owned_gpu_render_sky;f.argtypes=ns['api'].argtypes
 probe=getattr(d,'nf_sky_vertex_buffer_stats',None)
 if probe:probe.argtypes=[C.c_void_p]
 try:
  for weight in (0,.2,.4,.6,.8,.99):
   assert f(ns['frame'],len(ns['raw']),ns['a'],ns['b'],15136,weight,ns['out'],len(ns['out']))==0
   digest=hashlib.sha256(ns['out'].raw).hexdigest()
   if weight in expected:assert digest==expected[weight],(weight,'Pixel mismatch')
   else:expected[weight]=digest
   if probe:
    s=(C.c_uint64*2)();assert probe(s);stats.append(dict(weight=weight,bytes=s[0],allocations=s[1]))
    assert s[0]==(0 if weight==0 else 15136*8*24) and s[1]==(0 if weight==0 else 1)
   checks.append(dict(renderer=name,weight=weight,rgb_sha256=digest))
 finally:assert d.nf_owned_gpu_close()
 if probe:
  s=(C.c_uint64*2)();assert probe(s) and s[0]==0 and s[1]==1
  assert f(ns['frame'],len(ns['raw']),ns['a'],ns['b'],15136,.4,ns['out'],len(ns['out']))==0
  assert probe(s) and s[0]==15136*8*24 and s[1]==2
  assert hashlib.sha256(ns['out'].raw).hexdigest()==expected[.4]
  assert d.nf_owned_gpu_close() and probe(s) and s[0]==0
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-buffer-reuse-20261008');cp.mkdir(exist_ok=True)
(cp/'gpu-parity.json').write_text(json.dumps(dict(result='PASS',checks=checks,buffer_stats=stats,reopen_verified=True,scope='Six full4K background outputs exact, one bounded allocation reused per GPU lifetime, freed on close/reallocated on reopen. Not full-scene live or cadence proof.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print('PASS full4K pixels and sky buffer ownership/reopen')
