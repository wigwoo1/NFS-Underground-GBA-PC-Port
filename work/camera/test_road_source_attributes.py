"""Owned raw road UV inputs against captured source bytes and command reader."""
from pathlib import Path
import ctypes as C,struct,json,sys,runpy
sys.path.insert(0,'work/camera');from scene_batches import records
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
class Attributes(C.Structure):_fields_=[('count',C.c_uint32),('shift',C.c_uint32),('stored_height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
assert C.sizeof(Attributes)==288
fn=d.nf_road_source_attributes_owned;fn.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p]
command_fn=d.nf_scene_command_road_attributes_owned;command_fn.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();cases=failures=0
for event in records(p/'world.bin'):
 if event['pc']!=0x030032f0:continue
 blocks=event['blocks'];desc=blocks[4][1]
 if struct.unpack_from('<H',desc,4)[0] or not struct.unpack_from('<H',desc,8)[0]:continue
 reads=[];failed=[None]
 @Read
 def read(ctx,address,out,size):
  reads.append((address,size))
  if failed[0]==len(reads)-1:return 0
  for base,data in list(blocks.values())+[(0x08000000,rom)]:
   if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
  return 0
 affine=struct.unpack_from('<I',blocks[69][1])[0];out=Attributes()
 assert fn(read,None,blocks[1][0],blocks[4][0],affine,C.byref(out)),event['id']
 count=struct.unpack_from('<H',desc,2)[0];src=blocks[5][1];animation=blocks[9][1]
 assert out.count==count and out.shift==struct.unpack_from('<H',blocks[8][1],36)[0] and out.stored_height==struct.unpack_from('<H',blocks[8][1],38)[0] and out.affine==affine
 assert out.animation==blocks[9][0] and list(out.offsets)==list(struct.unpack_from('<2h',animation,4))
 assert [list(out.attributes[i]) for i in range(count)]==[list(struct.unpack_from('<2i',src,i*68+32)) for i in range(count)]
 assert all(list(out.attributes[i])==[0,0] for i in range(count,32))
 # Every consumed read failure must reject the complete metadata atomically.
 steps=len(reads)
 for step in range(steps):
  failed[0]=step;reads.clear();sentinel=C.create_string_buffer(b'X'*288,288)
  assert not fn(read,None,blocks[1][0],blocks[4][0],affine,sentinel) and sentinel.raw==b'X'*288;failures+=1
 cases+=1
sys.argv=['oracle','0.5','motion','road-full'];n=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));command_cases=0
for command in n['commands']:
 if command.kind!=1:continue
 out=Attributes();assert command_fn(C.byref(command),n['immutable_reader'],None,C.byref(out))
 assert out.affine==command.xyz[1] and out.material==command.material[0] and out.shift==command.material[2] and out.stored_height==command.material[3]
 bad=n['NativeCommand'].from_buffer_copy(bytes(command)) if 'NativeCommand' in n else type(command).from_buffer_copy(bytes(command))
 bad.material[0]^=32;sentinel=C.create_string_buffer(b'X'*288,288)
 assert not command_fn(C.byref(bad),n['immutable_reader'],None,sentinel) and sentinel.raw==b'X'*288
 command_cases+=1
report=dict(result='PASS',captured_roads=cases,failed_read_atomic_rejections=failures,owned_command_cases=command_cases,metadata_bytes=288,scope='Raw source UV/material/animation inputs copied and validated against captured bytes; current immutable owned command reader plus altered-material identity rejection. No packet serialization or live correction integration yet.')
(p/'road-source-attributes-tests.json').write_text(json.dumps(report,indent=2));print(report)
