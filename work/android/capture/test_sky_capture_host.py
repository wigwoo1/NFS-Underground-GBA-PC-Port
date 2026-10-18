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

skyen=api('capture_sky_enable',[P,C.c_int]);sky=api('capture_sky',[P,Q,U,P,S],S);bundle=api('capture_bundle',[P,Q,U,P,S],S)
sky_scene=api('capture_sky_scene',[P,Q,U,P,S],S);joined_counts={1:0,2:0};joined_sizes=[]
rompath=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';rom=rompath.read_bytes();h=op(os.fsencode(rompath));assert h
state=(root/'work/integration-0.state').read_bytes();seen={};missing=set();samples=0;ah=hashlib.sha256();last=None
try:
 assert not skyen(h,1) and not sky(h,0,0,None,0)
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and skyen(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as reference:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0))==1
   assert C.string_at(pixels(h),153600)==reference.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   pcm=C.create_string_buffer(16384);n=audio(h,pcm,4096);samples+=n;ah.update(pcm.raw[:n*4])
   info=(Q*5)();assert infof(h,info);n=bundle(h,info[0],info[1],None,0)
   if not n:continue
   data=C.create_string_buffer(n);assert bundle(h,info[0],info[1],data,n)==n;header=struct.unpack_from('<16Q',data.raw)
   joined_size=sky_scene(h,info[0],info[1],None,0);assert joined_size>0
   joined=C.create_string_buffer(bytes([165])*joined_size,joined_size)
   assert not sky_scene(h,info[0],info[1],joined,joined_size-1) and joined.raw==bytes([165])*joined_size
   assert not sky_scene(h,info[0]+1,info[1],joined,joined_size) and joined.raw==bytes([165])*joined_size
   assert sky_scene(h,info[0],info[1],joined,joined_size)==joined_size
   jh=struct.unpack_from('<16Q',joined.raw);assert jh[:8]==(0x3142534e,1,joined_size,info[0],info[1],header[5],header[6],header[7])
   assert jh[8:10]==(128,n) and joined.raw[128:128+n]==data.raw and jh[14:]==(0,0)
   for owner_index in range(header[7]):
    off,size=jh[10+owner_index*2:12+owner_index*2];assert size==30568 and off==128+n+owner_index*30568
    record=joined.raw[off:off+15192];sk=struct.unpack_from('<14I',record);origin=sk[9]-0x08000000
    assert joined.raw[off+15192:off+30568]==rom[origin:origin+15376]
   if header[7]==1:assert jh[12:14]==(0,0)
   joined_counts[header[5]]+=1;joined_sizes.append(joined_size)
   if joined_counts[header[5]]==1:(out/('sky-scene-whole.nsb' if header[5]==1 else 'sky-scene-split.nsb')).write_bytes(joined.raw)

   for part in range(header[7]):
    offset=header[8+part*2];serial,begin,end=struct.unpack_from('<3I',data.raw,offset+16);key=(info[0],serial)
    if key in seen:continue
    size=sky(h,*key,None,0)
    if not size:missing.add(key);continue
    assert size==15192;copy=C.create_string_buffer(bytes([165])*size,size)
    assert not sky(h,*key,copy,size-1) and copy.raw==bytes([165])*size
    assert not sky(h,info[0]+1,serial,copy,size) and copy.raw==bytes([165])*size
    assert sky(h,*key,copy,size)==size
    words=struct.unpack_from('<14I',copy.raw);epoch=words[2]|words[3]<<32
    assert words[0]==0x4b53464e and words[1]==1 and epoch==info[0] and begin<=words[4]<=end
    source=words[8]-0x08000000;assert copy.raw[56:]==rom[source:source+15136]
    expected=words[9]+(((((words[5]&16383)*240)>>12)%240-struct.unpack_from('<i',copy.raw,48)[0])&~1)
    assert words[8]==expected and words[11]==15136
    seen[key]=hashlib.sha256(copy.raw).hexdigest();last=key;(out/'captured-live-sky.bin').write_bytes(copy.raw)
 assert samples==443007 and ah.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert load(h,state,len(state))
 if last:assert not sky(h,*last,None,0) and not sky_scene(h,last[0],info[1],None,0)
finally:close(h)
assert joined_counts=={1:481,2:113}
report=dict(joined_whole=joined_counts[1],joined_split=joined_counts[2],min_bundle_bytes=min(joined_sizes),max_bundle_bytes=max(joined_sizes),result='PASS_SKY_SOURCE_CAPTURE_REPLAY',original_frames=600,original_timing=True,audio_frames=samples,audio_sha256=ah.hexdigest(),unique_sky_scenes=len(seen),missing_scene_keys=len(missing-set(seen)),source_bytes_equal_rom=True,android_runtime=False,paired_palette=True)
(out/'sky-source-capture-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert seen,'No positive original sky captures'

