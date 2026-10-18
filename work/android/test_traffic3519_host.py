"""Windows read-only component witness; compare separately with Android later."""
from pathlib import Path
import ctypes as C,hashlib,json,os,struct
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');candidate=base/'NFSUG-Android-Traffic-20261017';out=candidate/'host3519-results';out.mkdir(exist_ok=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(candidate/'native/capture-host.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t
def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pause=api('pause',[P,C.c_int]);timing=api('timing',[P,C.POINTER(Q)]);pixels=api('pixels',[P],P);audio=api('read_audio',[P,P,S],S)
enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);worlden=api('capture_source_world_enable',[P,C.c_int]);wallen=api('capture_wall_history_enable',[P,C.c_int]);skyen=api('capture_sky_enable',[P,C.c_int]);stats=api('capture_stats',[P,C.POINTER(Q)]);info=api('capture_layer_info',[P,C.POINTER(Q)])
bg=api('capture_background_scene',[P,Q,U,P,S],S);bundle=api('capture_bundle',[P,Q,U,P,S],S)
components={name:api('capture_'+suffix,[P,Q,U,U,U,P,S],S) for name,suffix in [('world','source_world'),('road','road_history'),('wall','wall_history'),('proof','write_ownership')]}
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();statebuf=C.create_string_buffer(state);keys=json.loads((base/'NFSUG-Android-Context-Refresh-20261017/route-results/input-keys.json').read_text())[:3540];pcm=(C.c_int16*8192)();baseline=[];runs=[];witness=None;frozen={}
def freeze(name,fn,args):
 size=fn(*args,None,0);entry=dict(present=bool(size),bytes=size)
 if size:
  assert size<=64*1024*1024;buffer=C.create_string_buffer(size);assert fn(*args,buffer,size)==size;data=buffer.raw;(out/name).write_bytes(data);entry['sha256']=hashlib.sha256(data).hexdigest();frozen[name]=entry['sha256'];return entry,data
 return entry,None
for captured in [False,True]:
 h=op(os.fsencode(rom));assert h;frames=hashlib.sha256();sound=hashlib.sha256();samples=0;missing=[]
 try:
  assert load(h,statebuf,len(state)) and pause(h,0)
  if captured:assert enable(h,1) and layers(h,1) and worlden(h,1) and wallen(h,1) and skyen(h,1)
  initial=(Q*4)();assert timing(h,initial)
  for i,key in enumerate(keys,1):
   assert step(h,key)==1;t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i and t[3]==i
   digest=hashlib.sha256(C.string_at(pixels(h),153600)).digest();frames.update(digest)
   if captured:assert digest==baseline[i-1],('original pixels',i)
   else:baseline.append(digest)
   n=audio(h,pcm,4096);assert n<=4096;sound.update(C.string_at(pcm,n*4));samples+=n
   if captured:
    layer=(Q*5)();assert info(h,layer);size=bg(h,layer[0],layer[1],None,0)
    if not size:missing.append(i)
    if i==3519:
     st=(Q*8)();assert stats(h,st);witness=dict(step=i,timing=list(t),layer_info=list(layer),capture_stats=list(st),owners=[])
     witness['background'],_=freeze('background.bin',bg,[h,layer[0],layer[1]])
     witness['bundle'],data=freeze('bundle.bin',bundle,[h,layer[0],layer[1]])
     if data:
      hdr=struct.unpack_from('<16Q',data);assert hdr[0]==0x3142414e and hdr[2]==len(data) and hdr[7] in [1,2]
      witness['kind']=hdr[5];witness['split_row']=hdr[6]
      for owner in range(hdr[7]):
       at,count=hdr[8+owner*2:10+owner*2];assert 128<=at and at+count<=len(data);serial,begin,end=struct.unpack_from('<3I',data,at+16);item=dict(owner=owner,serial=serial,begin=begin,end=end)
       for name,fn in components.items():item[name],_=freeze('owner'+str(owner)+'-'+name+'.bin',fn,[h,layer[0],serial,begin,end])
       witness['owners'].append(item)
     after=(Q*4)();assert timing(h,after) and list(after)==list(t) and hashlib.sha256(C.string_at(pixels(h),153600)).digest()==digest and audio(h,pcm,4096)==0
   if i%600==0:print(json.dumps(dict(phase='native' if captured else 'original',step=i,missing_background=len(missing))),flush=True)
  if captured:
   assert missing==list(range(1,11)) and witness['background']['present'] and witness['bundle']['present'] and witness['owners']
   assert all(owner[k]['present'] for owner in witness['owners'] for k in ['world','road','wall','proof'])
   traffic=d.nf_android_traffic_rotation_stats;traffic.argtypes=[C.POINTER(Q)];traffic.restype=C.c_int;counts=(Q*6)();assert traffic(counts) and counts[0]>0 and counts[1]>0;witness['traffic_stats']=list(counts)
   assert load(h,statebuf,len(state));reset=(Q*6)();assert traffic(reset) and list(reset)==[0]*6
   assert not bg(h,witness['layer_info'][0],witness['layer_info'][1],None,0)
   assert enable(h,0) and load(h,statebuf,len(state)) and pause(h,0)
   for index,key in enumerate(keys[:16]):assert step(h,key)==1 and hashlib.sha256(C.string_at(pixels(h),153600)).digest()==baseline[index]
  runs.append(dict(capture=captured,steps=len(keys),frame_hash_chain=frames.hexdigest(),audio_frames=samples,audio_sha256=sound.hexdigest(),missing_background_steps=missing))
 finally:close(h)
assert runs[0]['frame_hash_chain']==runs[1]['frame_hash_chain'] and runs[0]['audio_frames']==runs[1]['audio_frames'] and runs[0]['audio_sha256']==runs[1]['audio_sha256']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((base/'NFSUG-Android-Context-Refresh-20261017/host3519-results/host3519-report.json').read_text());assert runs[0]==previous['runs'][0]
report=dict(traffic_recovery_verified=True,traffic_reset_stale_epoch_detach_verified=True,result='VERIFIED_WINDOWS_HOST_TRAFFIC3519_RECOVERED',runs=runs,step3519=witness,frozen_component_sha256=frozen,host_dll_sha256=sha(candidate/'native/capture-host.dll'),test_sha256=sha(Path(__file__)),original_pixels_pcm_clocks_exact=True,limits='Windows capture queries original background every step and components at3519; does not reproduce all Java retained-scene queries. Android component correspondence must be checked separately. No GPU/audio-device/playable-performance proof.')
(out/'host3519-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(witness,indent=2),flush=True)
