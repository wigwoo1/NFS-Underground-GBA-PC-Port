"""Compare source scenery generation against original consumed matrices."""
import json,struct,random,ctypes as C
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import SceneryProjection
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791279461173682600.json').read_text());p=Path(r['model_pose_trace'])
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();projection=SceneryProjection(rom);store=OwnedModelBuilders(p.with_suffix('.builders.bin').read_bytes());poses=p.read_bytes();checks=0
for at in range(0,len(poses),292):
 h=struct.unpack_from('<8I',poses,at);model=struct.unpack_from('<h',poses,at+86)[0]
 if 31<=model<=36:
  value=store.at(h[3],h[5],h[1]);assert projection.matrix(value.camera,value.source,value.initial_matrix)==poses[at+244:at+292];checks+=1
assert checks==291
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(_,address,target,n):
 offset=address-0x08000000
 if not 0<=offset<=len(rom)-n:return 0
 C.memmove(target,rom[offset:offset+n],n);return 1
lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nf_object_projection_matrix;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p]
rng=random.Random(9926);values=[v for group in store.records.values() for v in group]
for _ in range(700):
 value=rng.choice(values);source=bytearray(value.source);camera=bytearray(value.camera)
 struct.pack_into('<3i',source,12,*(rng.randint(-2000000000,2000000000) for _ in range(3)))
 struct.pack_into('<2h',source,48,rng.randint(-32768,32767),rng.randint(-32768,32767));struct.pack_into('<H',source,10,rng.choice((0,2,4,6)))
 struct.pack_into('<12i',camera,0,*(rng.randint(-32768,32767) for _ in range(12)))
 output=C.create_string_buffer(value.initial_matrix,48);assert fn(bytes(camera),bytes(source),output,read,None)
 assert projection.matrix(bytes(camera),bytes(source),value.initial_matrix)==bytes(output)
print('PASS: 291 original consumed transforms, 700 native integer-builder comparisons')

source=bytearray(values[0].source);source[10]|=32
try:projection.matrix(values[0].camera,bytes(source),values[0].initial_matrix)
except ValueError:pass
else:raise AssertionError('External rotation accepted without owned RAM')
source=bytearray(values[0].source);struct.pack_into('<h',source,54,7)
try:projection.matrix(values[0].camera,bytes(source),values[0].initial_matrix)
except ValueError:pass
else:raise AssertionError('Player rotation treated as scenery')
print('PASS: unsupported rotation and player source rejection')
