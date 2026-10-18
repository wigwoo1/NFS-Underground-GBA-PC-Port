import json,tracemalloc,random
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
p=Path('work/camera');ns={};exec((p/'owned_closed_scene_memory.before-rom-direct.py').read_text(),ns);Old=ns['ClosedSceneMemory']
rom=bytes(range(256))*4096;rng=random.Random(1007);checks=0;peaks=[]
def memory(cls,ranges):
 m=cls.__new__(cls);m.rom=rom;m._ranges=tuple(ranges);m._starts=tuple(a for a,_ in ranges);m.missing=[];return m
for ranges in ([],[(0x08000010,b'xyz')],[(0x02000000,b'abc'),(0x08000010,b'xyz'),(0x08010000,b'q'*100)]):
 a,b=memory(Old,ranges),memory(ClosedSceneMemory,ranges)
 for address,size in [(0x08000000,16),(0x08000010,3),(0x0800000f,5),(0x08000013,16),(0x0800ffff,102),(0x02000001,5)]+[(0x08000000+rng.randrange(len(rom)-4096),rng.randrange(4096)) for _ in range(500)]:
  outcomes=[]
  for m in (a,b):
   try:outcomes.append(('ok',m.read(address,size)))
   except ValueError as e:outcomes.append(('error',str(e)))
  assert outcomes[0]==outcomes[1],(address,size);checks+=1
for cls in (Old,ClosedSceneMemory):
 m=memory(cls,[]);tracemalloc.start();data=m.read(0x08000000,524288);peaks.append(tracemalloc.get_traced_memory()[1]);tracemalloc.stop();assert data==rom[:524288]
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/scene-memory-rom-direct-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',read_checks=checks,baseline_peak_bytes=peaks[0],direct_peak_bytes=peaks[1],scope='Synthetic immutable ROM, captured overlays, boundary/gap/error parity; allocation measure for untouched512KiB ROM read, not live timing.'),indent=2))
for name in ('test_scene_memory_rom_direct.py','owned_closed_scene_memory.py','owned_closed_scene_memory.before-rom-direct.py'):(cp/name).write_bytes((p/name).read_bytes())
print('PASS',checks,'ROM/overlay reads; allocation peaks',peaks)
