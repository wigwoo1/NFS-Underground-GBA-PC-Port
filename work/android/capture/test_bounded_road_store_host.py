"""Road store replacement lifetime, malformed-command atomicity and source ownership."""
from pathlib import Path
import ctypes as C,subprocess,os,json,hashlib,struct
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=b/'NFSUG-road-store-component-local';out.mkdir(exist_ok=True);env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH'];subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(r/'work/camera/road_history_store.c'),'-o',str(out/'road-store.dll')],env=env,check=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'road-store.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t
class Event(C.Structure):_fields_=[('kind',U),('count',U),('shift',U),('address',U),('commands',P),('texture',P),('bytes',S),('read',P),('context',P)]
create=d.nf_road_history_create;create.argtypes=[Q,S];create.restype=P
append=d.nf_road_history_append;append.argtypes=[P,Q,Q,U,C.POINTER(Event)];append.restype=C.c_int
snapshot=d.nf_road_history_snapshot;snapshot.argtypes=[P,Q,P,S];snapshot.restype=S
stats=d.nf_road_history_stats;stats.argtypes=[P,C.POINTER(Q)];stats.restype=C.c_int
reset=d.nf_road_history_reset;reset.argtypes=[P,Q];reset.restype=C.c_int
destroy=d.nf_road_history_destroy;destroy.argtypes=[P]
h=create(1,131072);assert h;command=(U*17)();command[5]=0x08000000;command[6]=0x06000000;command[7]=130;command[16]=1;texture=(C.c_uint8*65536)();event=Event(1,1,0,0x08000000,C.cast(command,P),C.cast(texture,P),65536,None,None)
def read():
 n=snapshot(h,1,None,0);buf=C.create_string_buffer(n);assert snapshot(h,1,buf,n)==n;return buf.raw
try:
 for i in range(100000):texture[0]=i%251;assert append(h,1,i+1,i,C.byref(event))
 st=(Q*5)();assert stats(h,st) and list(st[:3])==[1,1,65536];before=read();texture[0]^=255;assert read()==before,'Borrowed texture retained';command[7]=513;assert not append(h,1,100001,100000,C.byref(event)) and read()==before;command[7]=130;assert not append(h,2,100001,100000,C.byref(event)) and not append(h,1,100000,100000,C.byref(event)) and read()==before
 tiny=C.create_string_buffer(b'unchanged');assert not snapshot(h,1,tiny,8) and tiny.raw.startswith(b'unchanged');assert not reset(h,0) and read()==before;assert reset(h,2) and not snapshot(h,1,None,0) and not snapshot(h,2,None,0)
finally:destroy(h)
report=dict(result='PASS_BOUNDED_ROAD_STORE_COMPONENT',replacement_runs=100000,retained_runs=1,asset_bytes=65536,snapshot_bytes=len(before),immutable_source_copy=True,invalid_epoch_order_width_capacity_atomic=True,reset_clears=True,source_hashes={name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in ['work/camera/road_history_store.c','work/camera/road_history_store.h']});(out/'component-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
