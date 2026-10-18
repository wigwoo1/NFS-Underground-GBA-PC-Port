"""Destination ownership vs two-sentinel committed execution, including same-value writes."""
from pathlib import Path
import ctypes as C,os,subprocess,json,hashlib,struct
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');out=b/'NFSUG-write-owner-component-local';out.mkdir(exist_ok=True);env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH']
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(r/'work/camera/write_ownership.c'),str(r/'work/camera/native_wall.c'),'-o',str(out/'ownership.dll')],env=env,check=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 d=C.CDLL(str(out/'ownership.dll'));oracle=C.CDLL(str(b/'NFSUG-android-wall-jni-native-local/capture-host.dll'))
P=C.c_void_p;U=C.c_uint32;Q=C.c_uint64;S=C.c_size_t
class Event(C.Structure):_fields_=[('kind',U),('count',U),('shift',U),('texture_address',U),('commands',P),('texture',P),('texture_size',S),('read',P),('context',P)]
create=d.nf_write_ownership_create;create.argtypes=[Q];create.restype=P
apply=d.nf_write_ownership_apply;apply.argtypes=[P,Q,U,C.POINTER(Event)];apply.restype=C.c_int
page=d.nf_write_ownership_page;page.argtypes=[P,Q,U,P,S];page.restype=S
reset=d.nf_write_ownership_reset;reset.argtypes=[P,Q];reset.restype=C.c_int
destroy=d.nf_write_ownership_destroy;destroy.argtypes=[P]
execute=oracle.nf_scene_execute;execute.argtypes=[C.POINTER(Event),U,P,S,C.POINTER(U)];execute.restype=C.c_int
Reader=C.CFUNCTYPE(C.c_int,P,U,P,S);payload=bytes(65536+4081);texture=C.create_string_buffer(payload)
@Reader
def read(context,address,destination,count):
 offset=address-0x08000000
 if offset<0 or offset+count>len(texture.raw):return 0
 C.memmove(destination,C.addressof(texture)+offset,count);return 1
h=create(1);assert h;expected_kind=bytearray(0x18000);expected_frame=[0]*0x18000;cases=0;checks=0

def submit(kind,words,count=1,shift=0,data=None):
 global texture,cases,checks
 if data is None:data=bytes(65536+4081)
 texture=C.create_string_buffer(bytes(data));commands=(U*len(words))(*words);e=Event(kind,count,shift,0x08000000,C.cast(commands,P),C.cast(texture,P),len(data),C.cast(read,P),None);outputs=[]
 for sentinel in (0x55,0xaa):
  v=(C.c_uint8*0x18000)(*([sentinel]*0x18000));writes=U();assert execute(C.byref(e),1,v,len(v),C.byref(writes)),('Oracle rejects',kind);outputs.append(bytes(v))
 frame=100+cases;assert apply(h,1,frame,C.byref(e));cases+=1
 for i in range(0x18000):
  if outputs[0][i]!=0x55 or outputs[1][i]!=0xaa:expected_kind[i]=kind;expected_frame[i]=frame
 for p in (0,1):
  result=C.create_string_buffer(192000);assert page(h,1,p,result,len(result))==192000;base=p*0xa000;assert result.raw[:38400]==expected_kind[base:base+38400];assert struct.unpack_from('<38400I',result.raw,38400)==tuple(expected_frame[base:base+38400]);checks+=38400
try:
 submit(4,[0,0x55555555,63]) # Equal to one sentinel: still a write.
 submit(6,[100,33])
 submit(5,[200,31,2,32,244])
 road=[0]*17;road[5]=0x08000000;road[6]=0x06000000;road[7]=2;road[16]=1;submit(1,road,data=bytes(4))
 model=[0,0x06000002,3,0,0,0,0];submit(3,model,shift=0,data=bytes(1)) # Model zero is opaque.
 wall=[0]*20;wall[2]=120;wall[4]=4;wall[9]=0x08000000;wall[11]=32768;wall[16]=0x7fff;wall[17]=0x06000000;wall[19]=3;data=bytearray(65536+4081);data[1]=7;data[2]=8;data[65536+8*16]=123;submit(2,wall,shift=1,data=data)
 # Other page, rawzero skip, zero width/rows and empty model commands.
 wall[17]=0x0600a001;submit(2,wall,shift=0,data=data[:65536]);submit(5,[0xffffffff,0,0,0,0]);submit(3,[0,0xffffffff,0,0,0,0,0],data=bytes(1));submit(3,[0],count=0,shift=12,data=bytes(1));submit(4,[0x18000,0,0])
 before=C.create_string_buffer(192000);page(h,1,0,before,len(before));bad=(U*14)(*([0,0x06000000,1,0,0,0,0]+[0,0x07000000,1,0,0,0,0]));e=Event(3,2,0,0x08000000,C.cast(bad,P),C.cast(texture,P),len(texture.raw),None,None);assert not apply(h,1,1000,C.byref(e));after=C.create_string_buffer(192000);page(h,1,0,after,len(after));assert before.raw==after.raw
 assert not apply(h,2,1000,C.byref(e)) and not page(h,2,0,None,0) and not page(h,1,2,None,0);tiny=C.create_string_buffer(b'unchanged');assert not page(h,1,0,tiny,8) and tiny.raw.startswith(b'unchanged');assert not reset(h,0) and reset(h,2);assert not page(h,1,0,None,0);assert page(h,2,0,after,len(after)) and after.raw==bytes(192000)
finally:destroy(h)
report=dict(result='PASS_SOURCE_WRITE_OWNERSHIP_COMPONENT',event_cases=cases,cell_kind_and_refresh_checks=checks,same_value_and_zero_writes=True,wall_rawzero_skip=True,invalid_range_rejects_atomically=True,reset_epoch_capacity_guards=True,source_hashes={name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in ['work/camera/write_ownership.c','work/camera/write_ownership.h']})
(out/'component-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

