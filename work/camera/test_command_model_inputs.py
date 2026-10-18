from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
Read=C.CFUNCTYPE(C.c_int,P,U,P,Z);Palette=C.CFUNCTYPE(C.c_int,P,U,P,Read,P,P,P);Inputs=C.CFUNCTYPE(C.c_int,P,U,P,P,P,P)
memory={};identity_rotation=struct.pack('<12i',16384,0,0,0,16384,0,0,0,16384,0,0,0);turn_rotation=struct.pack('<12i',0,0,16384,0,16384,0,-16384,0,0,0,0,0)
memory[0x02001000]=identity_rotation
descriptor=bytearray(40);struct.pack_into('<2H',descriptor,34,1,3);memory[0x08001000]=bytes(descriptor)
projection=bytearray(64);struct.pack_into('<2h',projection,8,120,80);memory[0x08001100]=bytes(projection)
memory[0x08001200]=struct.pack('<9h',-10,-10,0,10,-10,0,0,10,0);memory[0x08001300]=bytes([3]);memory[0x08001400]=struct.pack('<3H',0,1,2);memory[0x08001500]=struct.pack('<3H',0,1,2);memory[0x08001600]=struct.pack('<6H',0,0,32768,0,0,32768);memory[0x08001700]=bytes([1])
commands=(Command*2)();ids=(U*10)();colors=[]
for i in range(2):
 command=commands[i];source=0x02002000+i*164;command.head[0]=5;command.head[5]=source
 state=bytearray(256);struct.pack_into('<I',state,84,0x02001000);C.memmove(command.state,bytes(state),256)
 context=bytearray(68)
 for offset,value in [(8,0x08001100),(12,0x08001000),(16,0x08001200),(20,0x08001600),(32,0x08001400),(36,0x08001500),(44,0x08001300),(52,0x08001700),(64,128)]:struct.pack_into('<I',context,offset,value)
 struct.pack_into('<2H',context,56,0,1);C.memmove(command.model,bytes(context),68)
 obj=bytearray(164);struct.pack_into('<3i',obj,12,i*100*256,0,1000*256);memory[source]=bytes(obj)
 ids[i*5:i*5+5]=[3,0x02003000,source,0x08001000,0]
 palette=bytearray(512);struct.pack_into('<H',palette,2,31 if i==0 else 31<<10);colors.append(bytes(palette))
@Read
def reader(user,address,out,size):
 for base,blob in memory.items():
  if base<=address and address+size<=base+len(blob):C.memmove(out,blob[address-base:address-base+size],size);return 1
 return 0
palette_calls=[];input_calls=[];fail_second=False
@Palette
def palette(user,ordinal,command,read,context,rotation,out):palette_calls.append(ordinal);return 0
@Inputs
def inputs(user,ordinal,command,identity,rotation,out):
 input_calls.append(ordinal)
 if fail_second and ordinal==1:return 0
 assert C.string_at(identity,20)==bytes(ids)[ordinal*20:ordinal*20+20]
 C.memmove(rotation,identity_rotation if ordinal==0 else turn_rotation,48);C.memmove(out,colors[ordinal],512);return 1
fn=d.nf_assembly_commands_model_inputs;fn.argtypes=[P,U,P,P,C.c_double,Read,P,Palette,P,P,Inputs,P,U,U,U,U,P,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_free.argtypes=[P];table=bytes(131072);out=P();size=Z()
assert fn(commands,2,ids,None,0.5,reader,None,palette,None,bytes(48),inputs,None,1,100,104,0,table,C.byref(out),C.byref(size))
try:packet=C.string_at(out,size.value)
finally:d.nf_scene_packet_free(out)
offset,length=struct.unpack_from('<2I',packet,36);models=packet[offset:offset+length];assert struct.unpack_from('<2I',models)==(0x314c4d4e,2)
for i in range(2):
 offset,length=struct.unpack_from('<2I',models,8+i*8);model=models[offset:offset+length]
 assert struct.unpack_from('<3d',model,104)==(i*100,0,1000)
 assert model[-4:]==(bytes((255,0,0,255)) if i==0 else bytes((0,0,255,255)))
 quaternion=struct.unpack_from('<4d',model,128);assert (quaternion==(0,0,0,1))==(i==0)
assert input_calls==[0,1] and palette_calls==[]
fail_second=True;out=P(123);size=Z(456);assert not fn(commands,2,ids,None,0.5,reader,None,palette,None,bytes(48),inputs,None,1,100,104,0,table,C.byref(out),C.byref(size));assert (out.value,size.value)==(123,456)
report=dict(result='PASS',models=2,independent_rotation_position_palette=True,world_palette_not_substituted=True,missing_second_inputs_reject_atomically=True,scope='Native command extraction from bounded synthetic memory; per-object callback routing and atomic publication, not live paired regeneration.')
(p/'command-model-inputs-tests.json').write_text(json.dumps(report,indent=2));print(report)
