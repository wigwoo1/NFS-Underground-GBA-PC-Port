from pathlib import Path
import runpy,ctypes as C,struct,json
p=Path('work/camera');ns=runpy.run_path(str(p/'test_wall_write_states.py'));d=ns['d'];U=C.c_uint32;P=C.c_void_p
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
fn=d.nf_scene_command_wall_states_owned
fn.argtypes=[P,ns['Reader'],P,C.POINTER(P)]+[C.POINTER(U)]*3
command=Command();command.head[0]=2;command.head[10]=0x3000;command.head[11]=8;command.head[12]=1
owned=bytearray(256);struct.pack_into('<I',owned,80,0x2000);C.memmove(command.state,bytes(owned),256)
owned[:]=bytes(256)
checked=0
for flags,planes in ((0,17),(256,1)):
 command.head[6]=flags;ptr=P();w=U();h=U();n=U()
 assert fn(C.byref(command),ns['read'],None,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
 expected=bytes(2 if i else 0 for i in range(256))
 if planes==17:expected+=bytes(0 if not i else 2 if ns['table'][i*16+level] else 1 for level in range(16) for i in range(256))
 assert (w.value,h.value,n.value)==(256,1,planes)
 assert C.string_at(ptr,len(expected))==expected;d.nf_surface_free(ptr);checked+=len(expected)
guards=0
for kind,flags,shift,height in ((1,0,8,1),(2,128,8,1),(2,0,65544,1),(2,0,8,0),(2,0,8,65537)):
 command.head[0]=kind;command.head[6]=flags;command.head[11]=shift;command.head[12]=height
 ptr=P(123);w=U(41);h=U(42);n=U(43)
 assert not fn(C.byref(command),ns['read'],None,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
 assert (ptr.value,w.value,h.value,n.value)==(123,41,42,43);guards+=1
r=dict(result='PASS',owned_command_state_used=True,exact_classifications=checked,atomic_rejections=guards,scope='Shared command material overlay; base+16lighting owned classifications. Packet/assembly/live integration pending.')
(p/'command-wall-states-tests.json').write_text(json.dumps(r,indent=2));print(r)
