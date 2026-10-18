import ctypes as C,os,hashlib,json,struct,sys,subprocess
from pathlib import Path
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port'); out=Path(r'C:\NFSUG-Workspace\NFSUG-android-owned-text-local')
if os.environ.get('NF_TEST_RACING_OWNED_CAPTURE')!='1':
 env=os.environ.copy();env['NF_TEST_RACING_OWNED_CAPTURE']='1'
 raise SystemExit(subprocess.call([sys.executable,__file__],env=env))
with os.add_dll_directory(r'C:\msys64\mingw64\bin'): d=C.CDLL(str(out/'capture-owned-text-host.dll'))
def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
P=C.c_void_p; Q=C.c_uint64; U=C.c_uint; S=C.c_size_t
op=api('open',[C.c_char_p],P); close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P)
en=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);texten=api('capture_text_enable',[P,C.c_int]);infof=api('capture_layer_info',[P,C.POINTER(Q)]);txt=api('capture_text',[P,Q,U,P,S],S);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S)
diag=d.nf_owned_text_diagnostic;diag.argtypes=[Q,U,C.POINTER(Q)];diag.restype=C.c_int
glyphcount=d.nf_owned_text_glyph_count;glyphcount.restype=U
trace=d.nf_owned_text_trace;trace.argtypes=[C.c_char_p];trace.restype=C.c_int
h=op(os.fsencode(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'));assert h
state=(root/'work/integration-0.state').read_bytes(); found=covered=0; ah=hashlib.sha256(); samples=0;last=None;seen_epoch=None;epoch_resets=0
try:
 assert not txt(h,0,0,None,0) and not texten(h,1)
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and texten(h,1)
 assert trace(os.fsencode(out/'glyph-trace.csv'))
 ini=(Q*4)(); assert timing(h,ini)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as ref:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0))==1
   assert C.string_at(pixels(h),153600)==ref.read(153600),('frame',i)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==ini[2]+i+1 and t[3]==i+1
   pcm=C.create_string_buffer(16384);n=audio(h,pcm,4096);ah.update(pcm.raw[:n*4]);samples+=n
   info=(Q*5)();assert infof(h,info)
   if seen_epoch!=info[0]:
    assert texten(h,1);seen_epoch=info[0];epoch_resets+=1
   n=txt(h,info[0],info[1],None,0)
   if not n:
    if i==20:
     reason=(Q*12)();assert diag(info[0],info[1],reason);print('TEXT_REJECTION',list(reason),flush=True)
    continue
   assert n==76864;buf=C.create_string_buffer(bytes([165])*n,n)
   assert not txt(h,info[0],info[1],buf,n-1) and buf.raw==bytes([165])*n
   assert txt(h,info[0],info[1],buf,n)==n
   raw=buf.raw;assert struct.unpack_from('<8Q',raw)==(0x3154464e,1,n,info[0],info[1],240,160,1)
   assert set(raw[38464:])<={0,1};covered+=sum(raw[38464:]);found+=1;last=(info[0],info[1]);(out/'latest.nft').write_bytes(raw)
 assert samples==443007 and ah.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 glyph_calls=glyphcount();assert trace(None)
 if last:assert load(h,state,len(state)) and not txt(h,*last,None,0)
finally:close(h)
call_rows=(out/'glyph-trace.csv.calls.csv').read_text().splitlines()[1:]
raw_glyph_hits=sum(line.split(',')[2].lower()=='0806fc60' for line in call_rows)
report=dict(direct_call_records=len(call_rows),raw_glyph_target_hits=raw_glyph_hits,result='PASS_REPLAY_TEXT_API_DIAGNOSTIC',frames=600,original_pixels_identical=True,audio_frames=samples,audio_sha256=ah.hexdigest(),glyph_calls=glyph_calls,text_frames=found,covered_pixels=covered,epoch_reenables=epoch_resets,diagnostic_racing_flag=True,android_runtime=False)
(out/'owned-text-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))




