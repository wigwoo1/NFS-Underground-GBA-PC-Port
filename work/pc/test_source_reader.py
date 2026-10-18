from pathlib import Path
import ctypes as C,struct,hashlib,json,os,subprocess,threading
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-reader-tests';out.mkdir(exist_ok=True);fixtures=base/'NFSUG-background-owner-api-fixtures';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((base/'NFSUG-pc-source-frame-tests/build-report.json').read_text())
for name in ['source_frame.c','source_frame.h']:assert sha(source/name)==receipt['source_sha256'][name]
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(source/'source_frame.c'),str(source/'source_reader.c'),'-o',str(out/'source-reader.dll')];subprocess.run(cmd,check=True,env=env)
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
Info=C.CFUNCTYPE(I,P,C.POINTER(Q));BG=C.CFUNCTYPE(S,P,Q,U,P,S);Owner=C.CFUNCTYPE(S,P,Q,U,U,U,P,S)
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(n,args,r=I):f=getattr(dll,n);f.argtypes=args;f.restype=r;return f
bind=fn('nf_pc_source_api_bind_owner',[P]);op=fn('nf_pc_source_reader_open',[P,S],P);close=fn('nf_pc_source_reader_close',[P],None);capture=fn('nf_pc_source_reader_capture',[P,S],P);stats=fn('nf_pc_source_reader_info',[P,P]);free=fn('nf_pc_source_frame_free',[P],None);meta=fn('nf_pc_source_frame_info',[P,P]);part=fn('nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)])
def section(raw,index):at,n=struct.unpack_from('<2Q',raw,64+16*index);return raw[at:at+n]
def blob(frame,i,k):p=P();n=S();assert part(frame,i,k,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def addr(f):return C.cast(f,P).value
snapshots=raw_builds=components=0;inputs={}
for path in sorted(fixtures.glob('source-race-background-*.nrb')):
 source_bytes=path.read_bytes();original=(fixtures/path.name.removeprefix('source-')).read_bytes();epoch,refresh=struct.unpack_from('<2Q',original,24);nab=section(section(original,0),0);source_nab=section(section(source_bytes,0),0);count=struct.unpack_from('<Q',original,56)[0];data={'background':bytearray(original)};expected={};fault={'name':None};calls=[];inputs[str(path)]=sha(path)
 for owner in range(count):
  serial,begin,end,page=struct.unpack_from('<4I',section(nab,owner),16);key=(epoch,serial,begin,end)
  for kind,name,suffix in [(1,'geometry',None),(2,'road','nrh'),(3,'wall','nwh'),(4,'proof','nrp')]:
   raw=section(source_nab,owner) if suffix is None else (fixtures/f'owner-{serial}.{suffix}').read_bytes();data[name,key]=bytearray(raw);expected[owner,kind]=raw
 def copied(name,raw,dest,n):
  calls.append((name,bool(dest)));assert dest,'Reader called expensive raw size query'
  if fault['name']==name:return 0
  if fault['name']=='oversize':return 64*1024*1024+1
  if raw is None or n<len(raw):return 0
  C.memmove(dest,bytes(raw),len(raw));return len(raw)
 @Info
 def info(core,out):
  for i,v in enumerate([epoch,refresh,0,0,0]):out[i]=v
  return 1
 @BG
 def bg(core,e,r,dest,n):return copied('background',data['background'],dest,n) if (e,r)==(epoch,refresh) else 0
 callbacks=[]
 for name in ['geometry','road','wall','proof']:
  def make(name):
   @Owner
   def read(core,e,s,b,end,dest,n):return copied(name,data.get((name,(e,s,b,end))),dest,n)
   return read
  callbacks.append(make(name))
 api=API(C.sizeof(API),1,addr(info),addr(bg),*[addr(f) for f in callbacks],0);assert not op(C.byref(api),64*1024*1024);assert bind(C.byref(api));reader=op(C.byref(api),64*1024*1024);assert reader
 frame=capture(reader,64*1024*1024);assert frame;details=(Q*8)();assert meta(frame,details);st=(Q*8)();assert stats(reader,st) and st[1]==st[2]==1+4*count and st[3]==0;raw_builds+=st[1]
 assert blob(frame,0,0)==original
 for (owner,kind),raw in expected.items():assert blob(frame,owner,kind)==raw;components+=1
 assert not capture(reader,details[5]-1);exact=capture(reader,details[5]);assert exact;free(exact)
 for name in ['background','geometry','road','wall','proof','oversize']:
  fault['name']=name;assert not capture(reader,64*1024*1024)
 fault['name']=None;restored=capture(reader,64*1024*1024);assert restored;free(restored)
 wrong=[]
 def other_thread():
  sentinel=(Q*8)(*[77]*8);wrong.append(not capture(reader,64*1024*1024) and not stats(reader,sentinel) and list(sentinel)==[77]*8);close(reader)
 thread=threading.Thread(target=other_thread);thread.start();thread.join();assert wrong==[True];assert stats(reader,st)
 assert not op(C.byref(api),0) and not op(C.byref(api),64*1024*1024+1)
 tiny=op(C.byref(api),1);assert tiny and not capture(tiny,64*1024*1024);close(tiny);close(reader)
 for key in data:data[key][:]=bytes(len(data[key]))
 assert blob(frame,0,0)==original
 for (owner,kind),raw in expected.items():assert blob(frame,owner,kind)==raw
 free(frame);snapshots+=1
assert snapshots==9 and components==68 and raw_builds==77
r=dict(result='PASS_SOURCE_READER_SINGLE_BUILD_EXACT',snapshots=snapshots,owner_components=components,raw_packet_builds_first_captures=raw_builds,old_size_plus_copy_builds=raw_builds*2,all_callback_requests_have_output=True,frames_outlive_reader_and_inputs=True,exact_and_short_frame_budget=True,failed_read_recovery=True,wrong_thread_rejected_without_mutation=True,scratch_bytes=64*1024*1024,source_sha256={n:sha(source/n) for n in ['source_frame.c','source_frame.h','source_reader.c','source_reader.h','test_source_reader.py']},fixture_sha256=inputs,dll_sha256=sha(out/'source-reader.dll'),command=cmd,does_not_change_core=True)
(out/'reader-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','fixture_sha256','command']},indent=2))
