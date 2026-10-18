import ctypes as C,json,hashlib,struct
from dataclasses import replace
from pathlib import Path
setup=Path('work/camera/test_sky_concurrent_producer.py').read_text().split('import time,statistics')[0]
results=[]
for dll in ('owned-sky-gpu.dll','owned-sky-gpu-pingpong.dll')*3:
 env={};exec(compile(setup.replace('owned-sky-gpu.dll',dll),'hud-parity-setup','exec'),env)
 frame=env['frame'];h=struct.unpack_from('<6I2Q',frame);changed=bytearray(frame)
 for y in range(160):changed[40+h[2]+y*34944+128+32768]^=1
 checks=[]
 try:
  assert env['d'].nf_owned_gpu_window(0)==0
  for repeat in range(2):
   for variant,value in enumerate((frame,bytes(changed))):
    for weight in (0,.25,.5,.75,.999):
     env['samples']=replace(env['samples'],weight=weight)
     pixels=env['draw'](value);checks.append(dict(repeat=repeat,variant=variant,weight=weight,sha256=hashlib.sha256(pixels).hexdigest()))
 finally:assert env['d'].nf_owned_gpu_close()
 results.append(checks)
assert all(result==results[0] for result in results[1:]),'HUD target exchange changed complete rendered pixels'
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-target-exchange-candidate-20261006')
(out/'pixel-parity.json').write_text(json.dumps(dict(result='PASS',readbacks_per_context=len(results[0]),contexts_per_renderer=3,width=3840,height=2160,checks=results[0],scope='Exact full RGB image parity baseline versus candidate across sky weights, palette mutation and repeated alternating composition targets; not fullscene motion or sustained60fps proof'),indent=2));print('PASS exact4K fullimage parity',len(results[0]),'readbacks per renderer')

