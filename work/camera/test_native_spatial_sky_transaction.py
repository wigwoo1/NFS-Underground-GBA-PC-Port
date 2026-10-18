import ctypes as C,json,struct
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
source=Path('work/camera/test_native_draw_context.py').read_text();exec(source[source.index('class Draw'):source.index('gpu=C.CDLL')])
gpu=C.CDLL(str(Path('work/camera/owned-sky-spatial-runs.dll').resolve()));h=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()))
gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P];h.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=h.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
draw=C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();rgb=C.create_string_buffer(3840*2160*3);checks=[];q=None
try:
 assert gpu.nf_owned_gpu_window(0)==0
 for item in items:
  folder=Path(item['folder']);frame=(folder/'frame.bin').read_bytes();buf=C.create_string_buffer(frame);epoch=struct.unpack_from('<Q',frame,24)[0]
  older=SkyBoundary.decode((folder/'older-sky.bin').read_bytes());newer=SkyBoundary.decode((folder/'newer-sky.bin').read_bytes());origin=older.asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
  arrays={name:(C.c_double*(len((folder/(name+'.bin')).read_bytes())//8)).from_buffer_copy((folder/(name+'.bin')).read_bytes()) for name in ('camera','models','bounds')};count=len(arrays['bounds'])//4
  q=h.nf_owned_handoff_create(epoch)
  for index,alpha in enumerate((0,.5,1)):
   sky=asset.sample_continuous(older,newer,alpha);lo=C.create_string_buffer(sky.lower);hi=C.create_string_buffer(sky.upper)
   assert gpu.nf_owned_gpu_draw_scene_clips_sky(buf,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,lo,hi,15136,sky.weight)==0
   assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
   ctx=Draw(C.cast(buf,P),len(frame),C.cast(arrays['camera'],P),C.cast(arrays['models'],P),C.cast(arrays['bounds'],P),count,C.cast(lo,P),C.cast(hi,P),15136,sky.weight,-999,0,0,0);pc=Present(epoch,1,-999,0);sample=(U*8)();wait=(U*4)();stages=(U*7)()
   assert f(q,epoch,1,older.refresh,newer.refresh,index,alpha,0,draw,C.byref(ctx),present,C.byref(pc),sample,wait,stages)==1
   assert ctx.result==pc.result==0 and ctx.completed_ns<=sample[6]
   assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
   checks.append(dict(folder=str(folder),alpha=alpha,weight=sky.weight,full_rgb_exact=True))
  assert h.nf_owned_handoff_pause(q,1);ctx.result=pc.result=-999;sample=(U*8)(*([123]*8))
  assert f(q,epoch,1,older.refresh,newer.refresh,3,1,0,draw,C.byref(ctx),present,C.byref(pc),sample,wait,stages)==0
  assert ctx.result==pc.result==-999 and list(sample)==[123]*8
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(folder=str(folder),canceled_draw_and_present_not_invoked=True,last_rgb_unchanged=True))
  h.nf_owned_handoff_destroy(q);q=None
finally:
 if q:h.nf_owned_handoff_destroy(q)
 assert gpu.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-spatial-sky-transaction-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Recorded fullscene geometry with continuous sky phases through direct native transaction, exact4K parity versus same existing draw API, retired token preserves last image. Fixed geometry replay; live timing and independent fidelity remain unverified'),indent=2))
print('PASS native sky transaction',len(checks),'checks')

