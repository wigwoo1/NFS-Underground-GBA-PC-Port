import ctypes as C,json,struct
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
source=Path('work/camera/test_native_draw_context.py').read_text();exec(source[source.index('class Draw'):source.index('gpu=C.CDLL')])
gpu=C.CDLL(str(Path('work/camera/owned-sky-gpu.dll').resolve()));h=C.CDLL(str(Path('work/camera/owned-batch-ready-reuse-candidate.dll').resolve()))
gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P];h.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=h.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
draw=C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();rgb=C.create_string_buffer(3840*2160*3);checks=[];q=None

from owned_native_presentation_batch import OwnedPresentationBatch,BatchItem
batch=h.nf_owned_handoff_batch_ready;batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,CB,P]
h.nf_owned_batch_sample_size.restype=C.c_size_t;assert h.nf_owned_batch_sample_size()==C.sizeof(BatchItem)

import sys
report='work/camera/prototype-runs/owned-native-1791352541751468500.json'
sys.argv=['setup',report,'0','unused'];ns={}
exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'full-motion-setup','exec'),ns)
probe=C.CDLL(str(Path('work/camera/owned-dx-present-bridge.dll').resolve()));probe.nf_dx_bridge_diagnostic.argtypes=[P];interop_checks=[]
present=C.cast(probe.nf_dx_bridge_present_context_callback,CB)
try:
 assert gpu.nf_owned_gpu_window(1)==0
 adapter=C.CDLL(str(Path('work/camera/owned-gpu-ready-bounded-candidate.dll').resolve()));adapter.nf_gpu_ready_set_draw.argtypes=[P]
 assert adapter.nf_gpu_ready_set_draw(C.cast(draw,P))==0
 draw=C.cast(adapter.nf_gpu_ready_draw,CB);ready=C.cast(adapter.nf_gpu_ready_poll,CB)
 import threading
 rejected_adapter=[]
 def foreign_adapter():rejected_adapter.extend([adapter.nf_gpu_ready_poll(None),adapter.nf_gpu_ready_close()])
 foreign_thread=threading.Thread(target=foreign_adapter);foreign_thread.start();foreign_thread.join(5)
 assert not foreign_thread.is_alive() and rejected_adapter==[-1,31]
 source=json.loads(Path(report).read_text());boundaries=[]
 for scene in ns['scenes']:
  record=next(x for x in source['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,ns['rom'][offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,ns['rom'][origin-0x08000000:origin-0x08000000+15376]);epoch=boundaries[0].epoch;rows=[];images=[]
 import threading
 rejected=[]
 q=h.nf_owned_handoff_create(epoch)
 for index,alpha in enumerate((.1,.5,.9)):
  value=ns['prepared'].sample(alpha);sky=asset.sample_continuous(*boundaries,alpha);row=(*[b.refresh for b in boundaries],index,0,alpha,value,sky);rows.append(row)
  frame,camera,models,bounds,detail=value;fb=C.create_string_buffer(frame);lo=C.create_string_buffer(sky.lower);hi=C.create_string_buffer(sky.upper)
  assert gpu.nf_owned_gpu_draw_scene_clips_sky(fb,len(frame),camera,models,bounds,detail['geometry_records'],lo,hi,15136,sky.weight)==0
  stats=(U*4)();assert probe.nf_dx_bridge_present_callback(None)==1
  assert probe.nf_dx_bridge_stats(stats)==0 and stats[0]==index*3+1 and stats[1]==index and stats[2]==(index>0)
  out=(U*16)();result=probe.nf_dx_bridge_diagnostic(out)
  assert result==0 and out[8]==0 and out[9]==1 and out[11]==index*3+2 and probe.nf_dx_bridge_active()==1 and out[14]==0
  interop_checks.append(dict(alpha=alpha,result=result,values=list(out),before_diagnostic_stats=list(stats),native_callback_without_readback=True))
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw;images.append(expected)
  owned=OwnedPresentationBatch(epoch,[row]);assert batch(q,epoch,1,owned.items,1,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed),ready,None)==1
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(alpha=alpha,complete_motion_4k_rgb_exact=True,geometry_records=detail['geometry_records']))
 def foreign():
  out=(U*16)();rejected.append(probe.nf_dx_bridge_diagnostic(out))
 thread=threading.Thread(target=foreign);thread.start();thread.join(5);assert not thread.is_alive() and rejected==[31]
 assert len(set(images))>1,'Moving full scene produced identical images'
 h.nf_owned_handoff_destroy(q);q=h.nf_owned_handoff_create(epoch)
 owned=OwnedPresentationBatch(epoch,rows);assert batch(q,epoch,1,owned.items,3,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed),ready,None)==1 and owned.completed.value==3
 assert all(x.result==0 for x in owned.draws+owned.presents)
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[-1]
 checks.append(dict(full_motion_native_batch=3,final_4k_rgb_exact=True))
 stats=(U*4)();assert probe.nf_dx_bridge_stats(stats)==0 and list(stats)==[12,3,1,1]
 checks.append(dict(native_batch_dxgi_presentations=6,combined_presentations=12,diagnostic_readbacks=3))
 assert probe.nf_dx_bridge_close()==0 and probe.nf_dx_bridge_active()==0
 for index in range(3):
  out=(U*16)();assert probe.nf_dx_bridge_diagnostic(out)==0 and out[9]==1 and out[11]==index+1 and out[10]==0
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[-1]
 checks.append(dict(reopened_presentations=3,foreign_thread_without_context_rejected=rejected,idempotent_close=True))
finally:
 assert probe.nf_dx_bridge_close()==0 and probe.nf_dx_bridge_active()==0
 assert probe.nf_dx_bridge_close()==0
 if q:h.nf_owned_handoff_destroy(q)
 assert draw(C.byref(owned.draws[-1]))==0
 assert adapter.nf_gpu_ready_close()==0
 assert adapter.nf_gpu_ready_close()==0
 adapter.nf_gpu_ready_stats.argtypes=[P];resources=(U*4)();assert adapter.nf_gpu_ready_stats(resources)==0
 assert resources[0]==resources[1] and resources[3]==0
 print('GPU_READY_RESOURCES',list(resources))
 assert gpu.nf_owned_gpu_close()
 ns['prepared'].close();ns['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/dx-native-batch-present-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,interop_checks=interop_checks,scope='Captured9122->9126 reconstructed complete geometry/camera/model motion and recorded-angle ROM-derived sky. Exact4K parity versus existing renderer; not live timing/scanout or independent visual fidelity.'),indent=2));print('PASS complete motion native GPU batch',checks)
