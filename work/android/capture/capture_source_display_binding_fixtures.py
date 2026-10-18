"""Capture display fixtures for both scanout forms and all restored scene owners."""
import ctypes as C,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
flags=('NF_TEST_RACING_OWNED_CAPTURE','NF_CAPTURE_MODEL_VIEWS','NF_LIVE_ROAD_ATTRIBUTES')
if '--clean-child' not in sys.argv:
 env=os.environ.copy()
 for name in flags:env.pop(name,None)
 raise SystemExit(subprocess.call([sys.executable,__file__,'--clean-child'],env=env))
local=Path('C:/NFSUG-Workspace');root=Path('Y:/CODEX/NFSUG-Native-PC-Port');out=local/'NFSUG-source-display-binding-fixtures';out.mkdir(exist_ok=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(local/'NFSUG-android-source-world-jni-local/capture-host.dll'))
P=C.c_void_p;U=C.c_uint32;Q=C.c_uint64;S=C.c_size_t

def api(n,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+n);f.argtypes=args;f.restype=ret;return f
op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P)
enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);source_enable=api('capture_source_world_enable',[P,C.c_int]);source=api('capture_source_world',[P,Q,U,U,U,P,S],S)
info=api('capture_layer_info',[P,C.POINTER(Q)]);bundle=api('capture_bundle',[P,Q,U,P,S],S);audio=api('read_audio',[P,P,S],S)
state=(root/'work/integration-0.state').read_bytes();h=op(os.fsencode(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'));assert h
wanted={7,17,18,19,61,62,63,67,69};found=set();kinds=set();fixtures=[];pcm=(C.c_int16*8192)();eligible=0
try:
 assert load(h,state,len(state)) and enable(h,1) and layers(h,1) and source_enable(h,1)
 with (local/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   owner=(Q*5)()
   if not info(h,owner):continue
   size=bundle(h,owner[0],owner[1],None,0)
   if not size:continue
   raw=C.create_string_buffer(size);assert bundle(h,owner[0],owner[1],raw,size)==size;b=raw.raw;epoch,refresh,kind,cut,count=struct.unpack_from('<5Q',b,24);owners=[]
   for j in range(count):
    at,n=struct.unpack_from('<2Q',b,64+j*16);serial,begin,end,page=struct.unpack_from('<4I',b,at+16);owners.append((serial,begin,end,page))
   eligible+=1;needed=wanted.intersection(r[0] for r in owners)-found
   if kind in kinds and not needed:continue
   sources=[]
   for serial,begin,end,page in owners:
    n=source(h,epoch,serial,begin,end,None,0);assert n,('Source binding missing',epoch,serial,begin,end)
    data=C.create_string_buffer(n);assert source(h,epoch,serial,begin,end,data,n)==n
    name=f'source-{serial}.nsp';(out/name).write_bytes(data.raw);sources.append(dict(serial=serial,file=name,sha256=hashlib.sha256(data.raw).hexdigest()))
   name=f'display-{refresh}.nab';(out/name).write_bytes(b);fixtures.append(dict(file=name,epoch=epoch,refresh=refresh,kind=kind,split_row=cut,sources=sources,sha256=hashlib.sha256(b).hexdigest()));kinds.add(kind);found.update(r[0] for r in owners if r[0] in wanted)
finally:close(h)
assert kinds=={1,2} and found==wanted,(kinds,found)
report=dict(result='PASS_SOURCE_DISPLAY_BINDING_FIXTURES',original_frames=600,eligible_display_snapshots=eligible,fixtures=fixtures,restored_scene_owners=sorted(found),diagnostic_environment_required=False)
(out/'manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='fixtures'},indent=2));print('saved_fixtures',len(fixtures))
