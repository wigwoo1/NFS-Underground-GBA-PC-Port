import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');frames=[8758,8762,8766,8769,8773,8776,8780];outputs={};checks=[]
for name in ('owned-sky-source-context-candidate.dll','owned-sky-spatial-runs.dll'):
 d=C.CDLL(str((p/name).resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];out=C.create_string_buffer(3840*2160*3)
 try:
  for refresh in frames:
   data=(p/f'motion-actual-scanline-assets/{refresh}-native-complete-frame.bin').read_bytes();buf=C.create_string_buffer(data)
   assert d.nf_owned_gpu_draw(buf,len(data))==0
   assert d.nf_owned_gpu_read(out,len(out))==0
   digest=hashlib.sha256(out.raw).hexdigest()
   if refresh in outputs:assert digest==outputs[refresh],(refresh,'Unexpected non-sky rendering difference')
   else:outputs[refresh]=digest
   checks.append(dict(renderer=name,refresh=refresh,rgb_sha256=digest))
 finally:assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-spatial-runs-no-sky-parity-20261008');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,pixels_per_frame=8294400,scope='Seven complete captured frames without fractional sky attachment: rebuilt spatial candidate vs existing source DLL full RGB exact. Does not cover fractional sky/HUD interaction or live performance.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print('PASS seven full-scene frames unchanged without fractional sky attachment')

