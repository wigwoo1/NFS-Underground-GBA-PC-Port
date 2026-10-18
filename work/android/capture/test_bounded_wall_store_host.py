"""Bounded native wall retention vs immutable original history and hardware-owned fixtures."""
from pathlib import Path
import ctypes as C,os,struct,json,hashlib,subprocess,ast
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-wall-assets-fixtures';out=base/'NFSUG-bounded-wall-store-local';out.mkdir(exist_ok=True)
env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH'];subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(root/'work/camera/wall_history_store.c'),str(root/'work/camera/native_wall.c'),'-o',str(out/'wall-history-store.dll')],env=env,check=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'wall-history-store.dll'))
P=C.c_void_p;U=C.c_uint32;Q=C.c_uint64;S=C.c_size_t
class Event(C.Structure):_fields_=[('kind',U),('count',U),('shift',U),('texture_address',U),('commands',P),('texture',P),('texture_size',S),('read',P),('context',P)]
create=d.nf_wall_history_create;create.argtypes=[Q,S];create.restype=P
append=d.nf_wall_history_append;append.argtypes=[P,Q,Q,U,C.POINTER(Event)];append.restype=C.c_int
snapshot=d.nf_wall_history_snapshot;snapshot.argtypes=[P,Q,P,S];snapshot.restype=S
reset=d.nf_wall_history_reset;reset.argtypes=[P,Q];reset.restype=C.c_int
destroy=d.nf_wall_history_destroy;destroy.argtypes=[P]
stats=d.nf_wall_history_stats;stats.argtypes=[P,C.POINTER(Q)];stats.restype=C.c_int
# Reuse only the independent reader function, without running its capture verifier.
tree=ast.parse((root/'work/android/capture/verify_compact_wall_history_host.py').read_text());ns={'struct':struct};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse'],type_ignores=[]),'<independent-NWH-reader>','exec'),ns);parse=ns['parse']
def values(assets,events):
 state={}
 for e,c in events:
  shift=c[3];uvshift=15;texture=c[9];step=c[11]
  if c[6] and step>0x1b000:shift-=2;uvshift=17;texture=(texture+c[7])&0xffffffff
  texture=((texture+((c[13]&c[16])>>uvshift))&0xffffffff)&~1;dest=(c[17]+((c[2]*(c[1]>>14))<<1))&0xffffffff;vertical=c[18];mask=(c[4]<<15)-1;data=assets[e[4]][2]
  for row in range(c[19]):
   vertical&=mask;address=(texture+((vertical>>uvshift)<<shift))&0xffffffff;offset=address-e[6];index=data[offset]
   if index:
    if e[8]:index=assets[e[5]][2][index*16]
    for lane in range(2):
     page,cell=divmod((dest&~1)+lane-0x06000000,0xa000)
     if page in (0,1) and cell<38400:state[(page,cell)]=(index,e[3])
   dest=(dest+(c[2]<<1))&0xffffffff;vertical=(vertical+step)&0xffffffff
 return state
raw=(folder/'original-wall-history.nwh').read_bytes();header,assets,events=parse(raw);epoch=header[3];handle=create(epoch,32*1024*1024);assert handle
cursor=checks=peak_events=peak_assets=peak_bytes=0;snapshots=[]
def push(item):
 global peak_events,peak_assets,peak_bytes
 e,c=item;command=(U*20)(*c);payload=assets[e[4]][2]+(assets[e[5]][2] if e[8] else b'');texture=C.create_string_buffer(payload);event=Event(2,1,e[8],e[6],C.cast(command,P),C.cast(texture,P),len(payload),None,None);assert append(handle,epoch,e[2],e[3],C.byref(event));st=(Q*5)();assert stats(handle,st);peak_events=max(peak_events,st[0]);peak_assets=max(peak_assets,st[1]);peak_bytes=max(peak_bytes,st[2])
def read():
 n=snapshot(handle,epoch,None,0);assert n;buf=C.create_string_buffer(n);assert snapshot(handle,epoch,buf,n)==n;return buf.raw
capture=json.loads((folder/'source-fixture-capture-report.json').read_text())
try:
 for record in sorted(capture['road_records'],key=lambda r:r['owner']['end']):
  owner=record['owner']
  while cursor<len(events) and events[cursor][0][3]<=owner['end']:push(events[cursor]);cursor+=1
  bounded=read();h,a,e=parse(bounded);state=values(a,e);reference=values(assets,events[:cursor]);assert state==reference,'Pruning changed wall-source state';proof=(folder/record['provenance']['filename']).read_bytes();full=(folder/record['full_replay']['filename']).read_bytes()
  for cell in range(38400):
   if proof[cell]==2:assert state[(owner['page'],cell)]==(full[cell],struct.unpack_from('<I',proof,38400+cell*4)[0]);checks+=1
  name=f"owner-{owner['serial']}.nwh";(out/name).write_bytes(bounded);snapshots.append(dict(serial=owner['serial'],bytes=len(bounded),events=h[5],original_prefix_events=cursor,sha256=hashlib.sha256(bounded).hexdigest()))
 while cursor<len(events):
  push(events[cursor]);cursor+=1;st=(Q*5)();assert stats(handle,st);peak_events=max(peak_events,st[0]);peak_assets=max(peak_assets,st[1]);peak_bytes=max(peak_bytes,st[2])
 before=read();assert not snapshot(handle,epoch+1,None,0);tiny=C.create_string_buffer(b'unchanged');assert not snapshot(handle,epoch,tiny,8) and tiny.raw.startswith(b'unchanged')
 assert not reset(handle,0) and read()==before;assert reset(handle,epoch+1) and not snapshot(handle,epoch,None,0) and not snapshot(handle,epoch+1,None,0)
finally:destroy(handle)
# Repeated replacement must retire commands and immutable assets indefinitely.
h=create(1,2*65536);assert h;command=(U*20)();command[2]=0;command[3]=0;command[4]=1;command[9]=0x08000000;command[17]=0x06000000;command[19]=3;tex=(C.c_uint8*65536)();event=Event(2,1,0,0x08000000,C.cast(command,P),C.cast(tex,P),65536,None,None)
try:
 for i in range(100000):tex[0]=1+i%254;assert append(h,1,i+1,i,C.byref(event))
 st=(Q*5)();assert stats(h,st) and list(st[:3])==[1,1,65536];n=snapshot(h,1,None,0);assert n==64+64+65536+176
 before=C.create_string_buffer(n);snapshot(h,1,before,n);assert not append(h,1,100000,100000,C.byref(event));after=C.create_string_buffer(n);snapshot(h,1,after,n);assert before.raw==after.raw
 # Budget exhaustion must leave previous valid snapshot byte-exact.
 tex2=(C.c_uint8*(65536+4081))();tex2[0]=4;command[5]=0x02000000;shade=Event(2,1,1,0x08000000,C.cast(command,P),C.cast(tex2,P),len(tex2),None,None);assert not append(h,1,100001,100001,C.byref(shade));snapshot(h,1,after,n);assert before.raw==after.raw
finally:destroy(h)
assert checks==299970
jdk=base/'android-tools/jdk-21.0.12.1+1/bin';classes=out/'classes';test=root/'work/android/tests/org/codex/nfsugpreview/BoundedWallHistoryTest.java'
subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(root/'work/android/java'),'-d',str(classes),str(test)],check=True)
jr=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.BoundedWallHistoryTest',str(out),str(folder)],check=True,capture_output=True,text=True);print(jr.stdout,flush=True)
report=dict(result='PASS_BOUNDED_NATIVE_WALL_STORE',original_events=cursor,owner_checks=checks,snapshots=snapshots,peak_retained_events=peak_events,peak_assets=peak_assets,peak_asset_bytes=peak_bytes,replacement_events=100000,replacement_retained_events=1,replacement_asset_bytes=65536,atomic_budget_and_stale_rejections=True,reset_clears_history=True,live_hook_connected=False,java_result=jr.stdout.strip(),source_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['work/camera/wall_history_store.c','work/camera/wall_history_store.h','work/camera/native_wall.c','work/android/java/org/codex/nfsugpreview/NativeWallHistory.java','work/android/tests/org/codex/nfsugpreview/BoundedWallHistoryTest.java','work/android/capture/test_bounded_wall_store_host.py']})
(out/'bounded-wall-store-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('snapshots','source_hashes')},indent=2))
