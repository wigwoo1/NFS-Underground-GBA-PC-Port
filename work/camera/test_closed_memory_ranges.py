import random,json
from pathlib import Path
from types import MappingProxyType
from owned_closed_scene_memory import ClosedSceneMemory
rng=random.Random(62006);m=ClosedSceneMemory.__new__(ClosedSceneMemory);m.rom=bytes(range(256))*8;owned={0x08000000+i:(i+37)&255 for i in (0,3,64,65,66,511,1024,2047)};owned.update({0x02000000+i:i for i in range(16)});m._ranges=tuple((a,bytes((v,))) for a,v in sorted(owned.items()));m._starts=tuple(a for a,_ in m._ranges);m.owned_byte_count=len(owned);m.missing=[];checks=0
for _ in range(1000):
 offset=rng.randrange(len(m.rom)+1);size=rng.randrange(len(m.rom)-offset+1);address=0x08000000+offset;expected=bytes(owned.get(address+i,m.rom[offset+i]) for i in range(size));assert m.read(address,size)==expected;checks+=1
assert m.read(0x02000000,16)==bytes(range(16))
try:m.read(0x02000000,17)
except ValueError:pass
else:raise AssertionError('Unowned RAM read accepted')
try:m.owned[0x08000000]=0
except TypeError:pass
else:raise AssertionError('Read ownership mutable')
Path('work/camera/closed-memory-range-tests.json').write_text(json.dumps(dict(result='PASS_OWNED_ROM_RANGE_READS',random_overlay_ranges=checks,ram_gap_rejected=True,ownership_immutable=True),indent=2));print('PASS_OWNED_ROM_RANGE_READS',checks)
