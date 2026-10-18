"""Default optional-wall-OFF regression against last native build, exact packets/picture/clock/audio."""
from pathlib import Path
import ctypes as C,hashlib,os,json
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');state=(r/'work/integration-0.state').read_bytes();rom=r.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';results=[]
for folder in ('NFSUG-android-wall-jni-native-local','NFSUG-android-write-owner-native-local'):
 with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(b/folder/'capture-host.dll'))
 P=C.c_void_p;U=C.c_uint;Q=C.c_uint64;S=C.c_size_t
 def api(n,args,ret=C.c_int):
  f=getattr(d,'nfa_core_'+n);f.argtypes=args;f.restype=ret;return f
 op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S);enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);source=api('capture_source_world_enable',[P,C.c_int]);packet=api('capture_copy',[P,P,S],S)
 h=op(os.fsencode(rom));assert h;packets={};pcm=(C.c_int16*8192)();audiohash=hashlib.sha256();frames=0
 try:
  assert load(h,state,len(state)) and enable(h,1) and layers(h,1) and source(h,1);initial=(Q*4)();assert timing(h,initial)
  with (b/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
   for i in range(600):
    assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0)) and C.string_at(pixels(h),153600)==oracle.read(153600)
    t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
    while True:
     n=audio(h,pcm,4096)
     if not n:break
     frames+=n;audiohash.update(C.string_at(pcm,n*4))
    n=packet(h,None,0)
    if n:
     data=C.create_string_buffer(n);assert packet(h,data,n)==n;serial=int.from_bytes(data.raw[16:20],'little');digest=hashlib.sha256(data.raw).hexdigest()
     if serial in packets:assert packets[serial]==digest
     packets[serial]=digest
 finally:close(h)
 assert frames==443007 and audiohash.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 results.append(dict(packets=packets,audio_frames=frames,audio_sha256=audiohash.hexdigest()))
assert results[0]==results[1] and len(results[1]['packets'])==148
report=dict(result='PASS_WRITE_CAPTURE_DEFAULT_OFF_REGRESSION',frames_per_build=600,endpoint_packets=148,all_packet_bytes_equal=True,original_picture_timing_audio=True)
(b/'NFSUG-write-owner-api-fixtures/default-off-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
