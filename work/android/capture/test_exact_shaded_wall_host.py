import ctypes as C,json,os
from pathlib import Path
out=Path('C:/NFSUG-Workspace/NFSUG-android-exact-wall-replay-local')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-owned-text-host.dll'))
U=C.c_uint32;P=C.c_void_p;S=C.c_size_t
raw=d.nfs_wall_columns_write;raw.argtypes=[P,U,U,P,S,P,S,C.POINTER(U)];raw.restype=C.c_int
shade=d.nfs_wall_columns_write_shaded;shade.argtypes=[P,U,U,P,S,P,S,P,S,C.POINTER(U)];shade.restype=C.c_int
command=(U*20)();command[2]=120;command[3]=0;command[4]=4;command[9]=0x08000000;command[11]=1<<15;command[16]=0x7fff;command[17]=0x06000000;command[19]=3
texture=(C.c_uint8*65536)();texture[1]=7;texture[2]=8;lookup=(C.c_uint8*4081)();lookup[8*16]=123
vram=(C.c_uint8*0x18000)(*([0x55]*0x18000));written=U(0xdeadbeef);assert shade(command,1,0x08000000,texture,65536,lookup,4081,vram,len(vram),C.byref(written))==1 and written.value==2
assert bytes(vram[:2])==b'UU' and bytes(vram[240:242])==b'\0\0' and bytes(vram[480:482])==bytes([123,123])
positive={240,241,480,481};assert all(v==0x55 for i,v in enumerate(vram) if i not in positive)
C.memset(vram,0x55,len(vram));assert raw(command,1,0x08000000,texture,65536,vram,len(vram),C.byref(written))==1 and bytes(vram[240:242])==bytes([7,7]) and bytes(vram[480:482])==bytes([8,8])
for count,size in ((1,4080),(2,4081)):
 C.memset(vram,0x55,len(vram));assert shade(command,count,0x08000000,texture,65536,lookup,size,vram,len(vram),C.byref(written))==0 and bytes(vram)==bytes([0x55])*len(vram)
class Event(C.Structure):_fields_=[('kind',U),('count',U),('shift',U),('texture_address',U),('commands',P),('texture',P),('texture_size',S),('read',P),('context',P)]
payload=C.create_string_buffer(bytes(texture)+bytes(lookup));event=Event(2,1,1,0x08000000,C.cast(command,P),C.cast(payload,P),65536+4081,None,None)
execute=d.nf_scene_execute;execute.argtypes=[C.POINTER(Event),U,P,S,C.POINTER(U)];execute.restype=C.c_int
C.memset(vram,0x55,len(vram));assert execute(C.byref(event),1,vram,len(vram),C.byref(written)) and bytes(vram[240:242])==b'\0\0' and bytes(vram[480:482])==bytes([123,123])
for shift,length in ((2,65536+4081),(1,65536+4080)):
 event.shift=shift;event.texture_size=length;C.memset(vram,0x55,len(vram));assert not execute(C.byref(event),1,vram,len(vram),C.byref(written)) and bytes(vram)==bytes([0x55])*len(vram)
report=dict(result='PASS_ORIGINAL_SHADED_WALL_WRITE_SEMANTICS',zero_source_skips=True,nonzero_source_mapped_zero_writes_both_lanes=True,unshaded_api_preserved=True,invalid_lookup_count_and_event_payload_reject_atomically=True)
(out/'shaded-wall-component-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
