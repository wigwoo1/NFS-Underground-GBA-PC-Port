import ctypes as C,json,struct
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
source=Path('work/camera/test_native_draw_context.py').read_text();exec(source[source.index('class Draw'):source.index('gpu=C.CDLL')])
gpu=C.CDLL(str(Path('work/camera/owned-sky-gpu.dll').resolve()));h=C.CDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()))
gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P];h.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=h.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
draw=C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();rgb=C.create_string_buffer(3840*2160*3);checks=[];q=None

from owned_native_presentation_batch import OwnedPresentationBatch,BatchItem
batch=h.nf_owned_handoff_batch;batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P]
h.nf_owned_batch_sample_size.restype=C.c_size_t;assert h.nf_owned_batch_sample_size()==C.sizeof(BatchItem)
try:
 assert gpu.nf_owned_gpu_window(0)==0
 for item in items:
  folder=Path(item['folder']);frame=(folder/'frame.bin').read_bytes();epoch=struct.unpack_from('<Q',frame,24)[0]
  older=SkyBoundary.decode((folder/'older-sky.bin').read_bytes());newer=SkyBoundary.decode((folder/'newer-sky.bin').read_bytes());origin=older.asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
  arrays={name:(C.c_double*(len((folder/(name+'.bin')).read_bytes())//8)).from_buffer_copy((folder/(name+'.bin')).read_bytes()) for name in ('camera','models','bounds')};count=len(arrays['bounds'])//4
  rows=[(older.refresh,newer.refresh,index,0,alpha,(frame,arrays['camera'],arrays['models'],arrays['bounds'],dict(geometry_records=count)),asset.sample_continuous(older,newer,alpha)) for index,alpha in enumerate((0,.5,1))]
  final=rows[-1][-1];buf=C.create_string_buffer(frame);lo=C.create_string_buffer(final.lower);hi=C.create_string_buffer(final.upper)
  assert gpu.nf_owned_gpu_draw_scene_clips_sky(buf,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,lo,hi,15136,final.weight)==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  owned=OwnedPresentationBatch(epoch,rows);q=h.nf_owned_handoff_create(epoch)
  assert batch(q,epoch,1,owned.items,3,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed))==1 and owned.completed.value==3
  assert all(x.result==0 for x in owned.draws+owned.presents)
  assert [owned.samples[i*8+4] for i in range(3)]==[0,1,2]
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(folder=str(folder),native_samples=3,final_4k_rgb_exact=True))
  h.nf_owned_handoff_destroy(q);q=None
finally:
 if q:h.nf_owned_handoff_destroy(q)
 assert gpu.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-gpu-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Native callbacks, fixed fullscene geometry/continuous sky replay; exact final4K RGB versus existing draw API. No independent fidelity or sustained live timing proof.'),indent=2));print('PASS native complete-scene GPU batches',len(checks))
