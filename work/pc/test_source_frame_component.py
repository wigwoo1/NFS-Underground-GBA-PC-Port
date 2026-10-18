from pathlib import Path
import ctypes as C,struct,hashlib,json,os
base=Path(r'C:\NFSUG-Workspace');fixtures=base/'NFSUG-background-owner-api-fixtures';out=base/'NFSUG-pc-source-frame-tests'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-frame.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
Info=C.CFUNCTYPE(I,P,C.POINTER(Q));BG=C.CFUNCTYPE(S,P,Q,U,P,S);Owner=C.CFUNCTYPE(S,P,Q,U,U,U,P,S)
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
bind=dll.nf_pc_source_api_bind_owner;bind.argtypes=[C.POINTER(API)];bind.restype=I
cap=dll.nf_pc_source_frame_capture;cap.argtypes=[C.POINTER(API),S];cap.restype=P
free=dll.nf_pc_source_frame_free;free.argtypes=[P]
meta=dll.nf_pc_source_frame_info;meta.argtypes=[P,C.POINTER(Q)];meta.restype=I
owner=dll.nf_pc_source_frame_owner;owner.argtypes=[P,U,C.POINTER(Q)];owner.restype=I
part=dll.nf_pc_source_frame_component;part.argtypes=[P,U,U,C.POINTER(P),C.POINTER(S)];part.restype=I

def section(raw,index):at,n=struct.unpack_from('<2Q',raw,64+16*index);return raw[at:at+n]
def read_part(frame,i,k):ptr=P();size=S();assert part(frame,i,k,C.byref(ptr),C.byref(size));return C.string_at(ptr,size.value)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def copied(raw,dest,size):
 if not dest:return len(raw)
 if size<len(raw):return 0
 C.memmove(dest,bytes(raw),len(raw));return len(raw)
def address(function):return C.cast(function,P).value
snapshots=[];missing=malformed=budgets=0;whole=split=0;source_checks=0
for path in sorted(fixtures.glob('source-race-background-*.nrb')):
 source=path.read_bytes();original=(fixtures/path.name.removeprefix('source-')).read_bytes();epoch,refresh=struct.unpack_from('<2Q',original,24);nab=section(section(original,0),0);source_nab=section(section(source,0),0);count=struct.unpack_from('<Q',original,56)[0];rows={};expected={};data={'background':bytearray(original)};fault={'missing':None}
 for index in range(count):
  header=struct.unpack_from('<4I',section(nab,index),16);serial,begin,end,page=header;key=(epoch,serial,begin,end);rows[index]=key
  for kind,name,suffix in [(1,'geometry',None),(2,'road','nrh'),(3,'wall','nwh'),(4,'proof','nrp')]:
   raw=section(source_nab,index) if suffix is None else (fixtures/('owner-'+str(serial)+'.'+suffix)).read_bytes();data[(name,key)]=bytearray(raw);expected[index,kind]=raw
 @Info
 def info(core,result):
  for i,value in enumerate((epoch,refresh,0,0,0)):result[i]=value
  return 1
 @BG
 def background(core,e,r,dest,n):return copied(data['background'],dest,n) if (e,r)==(epoch,refresh) and fault['missing']!='background' else 0
 callbacks=[]
 for name in ('geometry','road','wall','proof'):
  def make(name):
   @Owner
   def callback(core,e,s,b,f,dest,n):
    raw=data.get((name,(e,s,b,f)));return copied(raw,dest,n) if raw is not None and fault['missing']!=name else 0
   return callback
  callbacks.append(make(name))
 api=API(C.sizeof(API),1,address(info),address(background),*[address(f) for f in callbacks],0);assert bind(C.byref(api)) and not bind(C.byref(api));frame=cap(C.byref(api),64*1024*1024);assert frame,('Valid frame rejected',path.name)
 try:
  details=(Q*8)();assert meta(frame,details) and tuple(details[:5])==struct.unpack_from('<5Q',original,24);assert read_part(frame,0,0)==original
  for i,key in rows.items():
   identity=(Q*5)();assert owner(frame,i,identity) and tuple(identity[:4])==key
   for kind in range(1,5):assert read_part(frame,i,kind)==expected[i,kind];source_checks+=1
  whole+=count==1;split+=count==2
  assert not cap(C.byref(api),details[5]-1);budgets+=1;exact=cap(C.byref(api),details[5]);assert exact;free(exact)
  for name in ('geometry','road','wall','proof'):
   fault['missing']=name;assert not cap(C.byref(api),64*1024*1024);missing+=1
  fault['missing']=None
  if not snapshots:
   changes=[('background',0,0),('background',24,epoch+1),('background',64,129)]
   first=rows[0]
   changes += [(('geometry',first),16,0xffffffff),(('road',first),24,epoch+1),(('wall',first),24,epoch+1),(('proof',first),32,0xffffffff)]
   for key,at,value in changes:
    prior=data[key][:];struct.pack_into('<Q' if key=='background' or at==24 or at==32 else '<I',data[key],at,value);assert not cap(C.byref(api),64*1024*1024),(key,at);data[key]=prior;malformed+=1
   bg=data['background'];nsb_at=struct.unpack_from('<Q',bg,64)[0];nrb_owner=struct.unpack_from('<Q',bg,80)[0];sky_at=nsb_at+struct.unpack_from('<Q',bg,nsb_at+80)[0]
   for at,value in [(nrb_owner+38480,2),(sky_at+15192+500,bg[sky_at+15192+500]^1)]:
    old=bg[at];bg[at]=value;assert not cap(C.byref(api),64*1024*1024);bg[at]=old;malformed+=1
   assert not cap(C.byref(api),64*1024*1024+1) and not cap(C.byref(api),0)
   wrong=API();C.memmove(C.byref(wrong),C.byref(api),C.sizeof(api));wrong.geometry=None;assert not cap(C.byref(wrong),64*1024*1024);wrong.size=1;assert not cap(C.byref(wrong),64*1024*1024)
   ptr=P(123);size=S(456);assert not part(frame,3,0,C.byref(ptr),C.byref(size)) and ptr.value==123 and size.value==456
  snapshots.append(dict(file=path.name,epoch=epoch,refresh=refresh,kind=details[2],owners=count,requested_bytes=details[5],background_sha256=digest(original)))
  for key in data:data[key][:]=bytes(len(data[key]))
  assert read_part(frame,0,0)==original
  for (i,k),raw in expected.items():assert read_part(frame,i,k)==raw
 finally:free(frame)
assert len(snapshots)==9 and missing==36 and malformed==9 and whole and split
result=dict(result='PASS_PC_SOURCE_FRAME_COMPONENT',snapshots=snapshots,whole=whole,split=split,source_components_equal=source_checks,missing_components_rejected=missing,malformed_rejected=malformed,exact_aggregate_budget_checks=budgets,caller_mutation_isolated=True,invalid_getter_output_unchanged=True,scope='Windows C join/ownership component against normal host source fixtures, not live core integration or rendering')
result['adapter_sha256']=hashlib.sha256((out/'source-frame.dll').read_bytes()).hexdigest()
result['source_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('source_frame.c','source_frame.h')}
result['test_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'component-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='snapshots'},indent=2))

