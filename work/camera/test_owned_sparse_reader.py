import ctypes as C,json,random
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
class Range(C.Structure):_fields_=[('address',C.c_uint32),('size',C.c_size_t),('data',C.c_void_p)]
class Reader(C.Structure):_fields_=[('rom',C.c_void_p),('rom_size',C.c_size_t),('ranges',C.POINTER(Range)),('count',C.c_size_t)]
d=C.CDLL(str(Path('work/camera/owned-sparse-reader.dll').resolve()));d.nf_owned_sparse_read.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t]
rng=random.Random(7);rom=bytes(rng.randrange(256) for _ in range(4096));ranges=((0x02000000,b'abcdefgh'),(0x02000008,b'ijklmnop'),(0x02000020,b'gap-end'),(0x08000010,b'overlay!'))
m=object.__new__(ClosedSceneMemory);m.rom=rom;m._ranges=ranges;m._starts=tuple(a for a,_ in ranges);m.missing=[]
backing=[C.create_string_buffer(data) for _,data in ranges];table=(Range*len(ranges))(*(Range(a,len(data),C.addressof(b)) for (a,data),b in zip(ranges,backing)));rom_buffer=C.create_string_buffer(rom);reader=Reader(C.addressof(rom_buffer),len(rom),table,len(table));passed=0;rejected=0
for address,size in [(0,0),(0x02000004,12),(0x02000000,17),(0x08000000,4096),(0xffffffff,2)]+[(rng.choice([0x02000000,0x08000000])+rng.randrange(0,4200),rng.randrange(0,100)) for _ in range(3000)]:
 output=C.create_string_buffer(b'Z'*max(1,size),max(1,size));before=output.raw
 try:expected=m.read(address,size)
 except ValueError:
  assert not d.nf_owned_sparse_read(C.byref(reader),address,output,size);assert output.raw==before;rejected+=1
 else:assert d.nf_owned_sparse_read(C.byref(reader),address,output,size) and output.raw[:size]==expected;passed+=1
result=dict(exact_reads=passed,atomic_rejections=rejected,scope='Native sparse read component; synthetic merged ranges, ROM overlays, holes and overflow. Live original scenes and integration still required.')
Path('work/camera/prototype-runs/native-sparse-reader.json').write_text(json.dumps(result,indent=2));print(result)
