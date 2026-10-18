# Candidate-only lifetime and live source-parity tests; production renderer unchanged.
from pathlib import Path
import ctypes as C,struct,hashlib,json,os,threading,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-reader-direct-tests';out.mkdir(exist_ok=True);fixtures=base/'NFSUG-background-owner-api-fixtures'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shim=out/'reader-protocol-shim.c';shim.write_text('#include "'+(here/'source_reader.c').as_posix()+'"\nNFPC_API size_t nf_pc_test_cached_packet(NFPCSourceReader*r,unsigned k,uint64_t e,unsigned serial,unsigned begin,unsigned end,void*out,size_t n){return packet(r,k,e,serial,begin,end,out,n); }\n')
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(here/'source_frame.c'),str(shim),'-o',str(out/'source-reader.dll')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(cmd,env=env,check=True)
receipt=dict(result='BUILT_MAINTAINED_SOURCE_READER_DIRECT',command=cmd,source_reader_dll_sha256=sha(out/'source-reader.dll'),source_sha256={n:sha(here/n) for n in ['source_frame.c','source_frame.h','source_reader.c','source_reader.h']})
(out/'reader-direct-build-report.json').write_text(json.dumps(receipt,indent=2))
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
Info=C.CFUNCTYPE(I,P,C.POINTER(Q));BG=C.CFUNCTYPE(S,P,Q,U,P,S);Owner=C.CFUNCTYPE(S,P,Q,U,U,U,P,S);Take=C.CFUNCTYPE(S,P,Q,U,C.POINTER(P));Release=C.CFUNCTYPE(None,P)
TakeOwner=C.CFUNCTYPE(S,P,Q,U,U,U,C.POINTER(P))
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(n,args,result=I):f=getattr(dll,n);f.argtypes=args;f.restype=result;return f
bind=fn('nf_pc_source_api_bind_owner',[P]);oldop=fn('nf_pc_source_reader_open',[P,S],P);op=fn('nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P);cap=fn('nf_pc_source_reader_capture',[P,S],P);close=fn('nf_pc_source_reader_close',[P],None);free=fn('nf_pc_source_frame_free',[P],None);meta=fn('nf_pc_source_frame_info',[P,P]);part=fn('nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)]);stats=fn('nf_pc_source_reader_info',[P,P]);ownedstats=fn('nf_pc_source_reader_owned_background_info',[P,P])
addr=lambda f:C.cast(f,P).value
def section(raw,i):at,n=struct.unpack_from('<2Q',raw,64+16*i);return raw[at:at+n]
def blob(frame,i,k):p=P();n=S();assert part(frame,i,k,C.byref(p),C.byref(n));return C.string_at(p,n.value)
snapshots=components=allocated=released=bytes_saved=0
for path in sorted(fixtures.glob('source-race-background-*.nrb')):
 source_bytes=path.read_bytes();original=(fixtures/path.name.removeprefix('source-')).read_bytes();epoch,refresh=struct.unpack_from('<2Q',original,24);nab=section(section(original,0),0);snab=section(section(source_bytes,0),0);count=struct.unpack_from('<Q',original,56)[0];data={'background':bytearray(original)};expected={};fault={'name':None,'take':'valid','geometry_take':'valid'};allocations={};release_errors=[];calls=[]
 for owner in range(count):
  serial,begin,end,page=struct.unpack_from('<4I',section(nab,owner),16);key=(epoch,serial,begin,end)
  for kind,name,suffix in [(1,'geometry',None),(2,'road','nrh'),(3,'wall','nwh'),(4,'proof','nrp')]:
   raw=section(snab,owner) if suffix is None else (fixtures/f'owner-{serial}.{suffix}').read_bytes();data[name,key]=bytearray(raw);expected[owner,kind]=raw
 @Info
 def info(core,output):
  for i,v in enumerate([epoch,refresh,0,0,0]):output[i]=v
  return 1
 def copied(name,raw,dest,n):
  calls.append(name)
  if fault['name']==name or raw is None:return 0
  if not dest:return len(raw)
  if n<len(raw):return 0
  C.memmove(dest,bytes(raw),len(raw));return len(raw)
 @BG
 def bg(core,e,r,dest,n):return copied('background',data['background'],dest,n) if (e,r)==(epoch,refresh) else 0
 callbacks=[]
 for name in ['geometry','road','wall','proof']:
  def make(name):
   @Owner
   def read(core,e,s,b,end,dest,n):return copied(name,data.get((name,(e,s,b,end))),dest,n)
   return read
  callbacks.append(make(name))
 @Take
 def take(core,e,r,pointer):
  global allocated
  pointer[0]=None
  if (e,r)!=(epoch,refresh) or fault['take']=='null':return len(original)
  raw=bytes(data['background'])
  if fault['take']=='corrupt':raw=bytes(8)+raw[8:]
  if fault['take']=='oversize':raw=b'x'
  buffer=C.create_string_buffer(raw,len(raw));address=C.addressof(buffer);allocations[address]=buffer;pointer[0]=address;allocated+=1
  return 0 if fault['take']=='zero' else 64*1024*1024+1 if fault['take']=='oversize' else len(raw)
 @TakeOwner
 def take_geometry(core,e,serial,begin,end,pointer):
  global allocated
  pointer[0]=None;raw=data.get(('geometry',(e,serial,begin,end)))
  if raw is None or fault['name']=='geometry':return 0
  mode=fault['geometry_take']
  if mode=='null':return len(raw)
  raw=bytes(raw)
  if mode=='corrupt':raw=bytes(8)+raw[8:]
  if mode=='oversize':raw=b'x'
  buffer=C.create_string_buffer(raw,len(raw));address=C.addressof(buffer);allocations[address]=buffer;pointer[0]=address;allocated+=1
  return 0 if mode=='zero' else 64*1024*1024+1 if mode=='oversize' else len(raw)
 @Release
 def release(pointer):
  global released
  if pointer not in allocations:release_errors.append(pointer);return
  allocations.pop(pointer);released+=1
 api=API(C.sizeof(API),1,addr(info),addr(bg),*[addr(f) for f in callbacks],0);assert bind(C.byref(api))
 old=oldop(C.byref(api),64*1024*1024);baseline=cap(old,64*1024*1024);assert baseline
 fields=(Q*8)();assert meta(baseline,fields);baseline_fields=list(fields);oldstats=(Q*8)();assert stats(old,oldstats)
 reader=op(C.byref(api),64*1024*1024,addr(take),addr(release),addr(take_geometry),addr(release));assert reader
 calls.clear();frame=cap(reader,64*1024*1024);assert frame and 'background' not in calls and 'geometry' not in calls
 assert meta(frame,fields) and list(fields)==baseline_fields;newstats=(Q*8)();assert stats(reader,newstats)
 removed=oldstats[4];assert newstats[0]==newstats[2]==newstats[4]==0;bytes_saved+=removed
 assert blob(frame,0,0)==blob(baseline,0,0)==original
 for (owner,kind),raw in expected.items():assert blob(frame,owner,kind)==blob(baseline,owner,kind)==raw;components+=1
 free(baseline);close(old)
 assert not cap(reader,fields[5]-1);exact=cap(reader,fields[5]);assert exact;free(exact)
 for mode in ['zero','null','oversize','corrupt']:
  fault['take']=mode;assert not cap(reader,64*1024*1024),(path.name,mode)
 fault['take']='valid'
 for mode in ['zero','null','oversize','corrupt']:
  fault['geometry_take']=mode;assert not cap(reader,64*1024*1024),(path.name,'geometry',mode)
 fault['geometry_take']='valid'
 for name in ['geometry','road','wall','proof']:
  fault['name']=name;assert not cap(reader,64*1024*1024)
 fault['name']=None;restored=cap(reader,64*1024*1024);assert restored;free(restored)
 assert not op(C.byref(api),64*1024*1024,None,addr(release),addr(take_geometry),addr(release)) and not op(C.byref(api),64*1024*1024,addr(take),None,addr(take_geometry),addr(release))
 wrong=[]
 def other_thread():
  v=(Q*3)(77,77,77);wrong.append(not cap(reader,64*1024*1024) and not ownedstats(reader,v) and list(v)==[77]*3);close(reader)
 worker=threading.Thread(target=other_thread);worker.start();worker.join();assert wrong==[True]
 v=(Q*3)();assert ownedstats(reader,v) and v[1]>0 and v[2]>0
 close(reader)
 for key in data:data[key][:]=bytes(len(data[key]))
 worker_result=[]
 def consume_after_reader_close():
  worker_result.append(blob(frame,0,0)==original and all(blob(frame,i,k)==raw for (i,k),raw in expected.items()));free(frame)
 worker=threading.Thread(target=consume_after_reader_close);worker.start();worker.join();assert worker_result==[True]
 assert not allocations and not release_errors;snapshots+=1
assert snapshots==9 and components==68 and allocated==released
result=dict(result='PASS_DIRECT_CACHED_FRAME_LIFETIMES',snapshots=snapshots,owner_components=components,allocations=allocated,releases=released,all_source_bytes_exact=True,reader_scratch_copy_bytes_removed_first_captures=bytes_saved,exact_and_short_budgets=True,zero_null_oversize_corrupt_inputs_release_safely=True,wrong_thread_capture_rejected=True,worker_reads_and_releases_after_reader_close=True,production_sources_changed=False,source_reader_dll_sha256=sha(out/'source-reader.dll'))
(out/'ownership-component-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)

subprocess.run([sys.executable,str(here/'test_source_reader_protocol.py')],check=True)
protocol=json.loads((out/'cached-protocol-report.json').read_text());assert protocol['dll_sha256']==receipt['source_reader_dll_sha256']
r=dict(result='PASS_MAINTAINED_SOURCE_READER_DIRECT',build_sha256=sha(out/'reader-direct-build-report.json'),ownership_sha256=sha(out/'ownership-component-report.json'),protocol_sha256=sha(out/'cached-protocol-report.json'),source_sha256=receipt['source_sha256'],dll_sha256=receipt['source_reader_dll_sha256'],test_sha256=sha(Path(__file__)),protocol_test_sha256=sha(here/'test_source_reader_protocol.py'))
(out/'reader-direct-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
