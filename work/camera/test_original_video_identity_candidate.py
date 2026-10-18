import ctypes as C,json,threading,hashlib
from pathlib import Path
d=C.CDLL(str(Path('work/camera/viewport-original-video-identity-candidate.dll').resolve()));P=C.c_void_p
for name,args,restype in [('nf_init',[C.c_char_p,C.c_char_p],C.c_int),('nf_state',[C.c_char_p,C.c_int],C.c_int),('nf_frame',[C.c_uint],None),('nf_pixels',[],P),('nf_native_scene_epoch',[],C.c_uint64),('nf_native_scene_refresh',[],C.c_uint),('nf_original_video_identity',[P],C.c_int),('nf_original_video_read',[C.c_uint64,C.c_uint,P,C.c_size_t],C.c_int)]:
 f=getattr(d,name);f.argtypes=args;f.restype=restype
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=Path('work/race.state');rows=[]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 ident=(C.c_uint64*4)();buf=C.create_string_buffer(153600)
 for i in range(12):
  d.nf_frame(1);assert d.nf_original_video_identity(ident)==1
  e,f=ident[:2];assert e==d.nf_native_scene_epoch();assert d.nf_original_video_read(e,f,buf,len(buf))==1
  assert buf.raw==C.string_at(d.nf_pixels(),153600)
  saved=buf.raw
  for epoch,refresh,size in [(e+1,f,len(buf)),(e,f+1,len(buf)),(e,f,len(buf)-1)]:
   assert d.nf_original_video_read(epoch,refresh,buf,size)==0 and buf.raw==saved
  wrong=[]
  t=threading.Thread(target=lambda:wrong.append(d.nf_original_video_read(e,f,buf,len(buf))));t.start();t.join();assert wrong==[0] and buf.raw==saved
  rows.append(dict(epoch=e,completed_refresh=f,current_refresh=d.nf_native_scene_refresh(),sha256=hashlib.sha256(saved).hexdigest()))
 old=ident[:2];assert d.nf_state(str(state).encode(),0)
 stale_read=d.nf_original_video_read(*old,buf,len(buf));stale_identity=d.nf_original_video_identity(ident)
 assert stale_read==0 and stale_identity==0
 d.nf_frame(1);assert d.nf_original_video_identity(ident)==1 and d.nf_original_video_read(*ident[:2],buf,len(buf))==1
 out=dict(result='PASS_ORIGINAL_VIDEO_IDENTITY_AND_RESET_GUARDS',rows=rows,stale_read_after_load=stale_read,stale_identity_after_load=stale_identity,scope='Original completed scanline snapshot equality to post-frame pixels and explicit ABI rejection guards; reset invalidation requires rejection before a new completed frame.')
 Path('outputs/nfsug-native-renderer/camera-research/original-video-identity-diagnostic-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:d.nf_close()
