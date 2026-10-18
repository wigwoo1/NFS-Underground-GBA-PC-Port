import ctypes as C,json,struct
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
source=Path('work/camera/test_native_draw_context.py').read_text();exec(source[source.index('class Draw'):source.index('gpu=C.CDLL')])
gpu=C.CDLL(str(Path('work/camera/owned-sky-queued-targets.dll').resolve()));h=C.CDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()))
gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P];h.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
f=h.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
draw=C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();rgb=C.create_string_buffer(3840*2160*3);checks=[];q=None

from owned_native_presentation_batch import OwnedPresentationBatch,BatchItem
batch=h.nf_owned_handoff_batch;batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P]
h.nf_owned_batch_sample_size.restype=C.c_size_t;assert h.nf_owned_batch_sample_size()==C.sizeof(BatchItem)

import sys
report='work/camera/prototype-runs/owned-native-1791352541751468500.json'
sys.argv=['setup',report,'0','unused'];ns={}
exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'full-motion-setup','exec'),ns)
probe=C.CDLL(str(Path('work/camera/owned-dx-present-bridge.dll').resolve()));probe.nf_dx_bridge_diagnostic.argtypes=[P];interop_checks=[]
present=C.cast(probe.nf_dx_bridge_present_context_callback,CB)
try:
 assert gpu.nf_owned_gpu_window(1)==0
 gpu.nf_owned_gpu_target_query_mode.argtypes=[C.c_int];assert gpu.nf_owned_gpu_target_query_mode(1)==0
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
  owned=OwnedPresentationBatch(epoch,[row]);assert batch(q,epoch,1,owned.items,1,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed))==1
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(alpha=alpha,complete_motion_4k_rgb_exact=True,geometry_records=detail['geometry_records']))
 def foreign():
  out=(U*16)();rejected.append(probe.nf_dx_bridge_diagnostic(out))
 thread=threading.Thread(target=foreign);thread.start();thread.join(5);assert not thread.is_alive() and rejected==[31]
 import hashlib
 assert [hashlib.sha256(x).hexdigest() for x in images]==json.loads(Path('work/camera/target-pool-reference.json').read_text()),'Target pool changed original renderer RGB'
 assert len(set(images))>1,'Moving full scene produced identical images'
 h.nf_owned_handoff_destroy(q);q=h.nf_owned_handoff_create(epoch)
 owned=OwnedPresentationBatch(epoch,rows);assert batch(q,epoch,1,owned.items,3,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed))==1 and owned.completed.value==3
 assert all(x.result==0 for x in owned.draws+owned.presents)
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[-1]
 checks.append(dict(full_motion_native_batch=3,final_4k_rgb_exact=True))
 stats=(U*4)();assert probe.nf_dx_bridge_stats(stats)==0 and list(stats)==[12,3,1,1]
 checks.append(dict(native_batch_dxgi_presentations=6,combined_presentations=12,diagnostic_readbacks=3))
 assert probe.nf_dx_bridge_close()==0 and probe.nf_dx_bridge_active()==0
 import time,statistics
 gpu.nf_owned_gpu_present_timed.argtypes=[U,P];gpu.nf_owned_gpu_present_stages.argtypes=[P];gpu.nf_owned_gpu_swap_interval.argtypes=[C.c_int,P]
 observed=(C.c_int*2)();assert gpu.nf_owned_gpu_swap_interval(0,observed)==0 and observed[1]==0
 ready_bridge=C.CDLL(str(Path('work/camera/owned-batch-ready-reuse-candidate.dll').resolve()))
 ready_batch=ready_bridge.nf_owned_handoff_batch_ready;ready_batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,CB,P]
 adapter=C.CDLL(str(Path('work/camera/owned-gpu-ready-adapter.dll').resolve()));adapter.nf_gpu_ready_set_draw.argtypes=[P]
 raw_draw=C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);assert adapter.nf_gpu_ready_set_draw(C.cast(raw_draw,P))==0
 ready_draw=C.cast(adapter.nf_gpu_ready_draw,CB);ready_poll=C.cast(adapter.nf_gpu_ready_poll,CB);gl_present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
 h.nf_owned_handoff_destroy(q);q=h.nf_owned_handoff_create(epoch)
 gpu.nf_owned_gpu_target_acquire.argtypes=[P];gpu.nf_owned_gpu_target_select.argtypes=[U,U];gpu.nf_owned_gpu_target_release.argtypes=[U]
 leases=[]
 for row,expected in zip(rows,images):
  owner=OwnedPresentationBatch(epoch,[row]);assert raw_draw(C.byref(owner.draws[0]))==0
  token=U();assert gpu.nf_owned_gpu_target_acquire(C.byref(token))==0;leases.append(token.value)
 blocked=OwnedPresentationBatch(epoch,[rows[0]]);assert raw_draw(C.byref(blocked.draws[0]))==39
 for token,expected in zip(leases,images):
  assert gpu.nf_owned_gpu_target_select(token,epoch+1)==32
  assert gpu.nf_owned_gpu_target_select(token,epoch)==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  assert gpu.nf_owned_gpu_present(epoch)==0
  assert gpu.nf_owned_gpu_target_release(token)==0
  assert gpu.nf_owned_gpu_target_select(token,epoch)==32 and gpu.nf_owned_gpu_target_release(token)==32
 checks.append(dict(three_queued_distinct_images_exact=True,pinned_overwrite_rejected=True,wrong_epoch_and_stale_tokens_rejected=True))
 queued=C.CDLL(str(Path('work/camera/owned-batch-queued-candidate.dll').resolve()))
 AC=C.CFUNCTYPE(C.c_int,C.POINTER(U));SC=C.CFUNCTYPE(C.c_int,U,U);RC=C.CFUNCTYPE(C.c_int,U)
 acquire=C.cast(gpu.nf_owned_gpu_target_acquire,AC);select=C.cast(gpu.nf_owned_gpu_target_select,SC);release=C.cast(gpu.nf_owned_gpu_target_release,RC);ready_token=C.cast(gpu.nf_owned_gpu_target_ready,RC)
 queued.nf_owned_handoff_create.argtypes=[U];queued.nf_owned_handoff_create.restype=P;queued.nf_owned_handoff_destroy.argtypes=[P]
 queue=queued.nf_owned_handoff_create(epoch);owners=OwnedPresentationBatch(epoch,rows);selected_images=[]
 @CB
 def exact_present(ctx):
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;selected_images.append(rgb.raw);return gl_present(ctx)
 queued.nf_owned_queued_set_query.argtypes=[P];assert queued.nf_owned_queued_set_query(C.cast(gpu.nf_owned_gpu_target_query,P))==1
 queued_batch=queued.nf_owned_handoff_batch_queued;queued_batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,AC,SC,RC,RC]
 try:
  assert queued_batch(queue,epoch,1,owners.items,3,raw_draw,exact_present,owners.samples,owners.waits,owners.stages,C.byref(owners.completed),acquire,select,release,ready_token)==1 and owners.completed.value==3
  assert selected_images==images
  queries=(U*64)();queued.nf_owned_queued_queries.argtypes=[P];assert queued.nf_owned_queued_queries(queries)==1
  assert len(set(queries[i*8] for i in range(3)))==3
  for i in range(3):
   qrow=list(queries[i*8:(i+1)*8]);assert qrow[0] and qrow[1]==epoch and qrow[2]<3 and qrow[3]<=qrow[4] and qrow[6]<=qrow[7]<=qrow[5]
 finally:queued.nf_owned_handoff_destroy(queue)
 checks.append(dict(native_draw_ahead_three_ordered_images_exact=True))

 prepared_owners=[]
 for j in range(120):
  alpha=.1+.8*j/119;value=ns['prepared'].sample(alpha);sky=asset.sample_continuous(*boundaries,alpha)
  row=(*[b.refresh for b in boundaries],0,0,alpha,value,sky);prepared_owners.append(OwnedPresentationBatch(epoch,[row]))
 assert prepared_owners[0].items[0].alpha==.1 and abs(prepared_owners[-1].items[0].alpha-.9)<1e-12
 records=[];origin=time.perf_counter_ns()
 for k in range(600):
  mode=(0,1,1,0)[(k//50)%4];deadline=origin+(k+1)*1000000000//60
  fixed=prepared_owners[k%120];fixed.items[0].index=k;fixed.items[0].deadline=deadline;fixed.completed.value=0
  begin=time.perf_counter_ns()
  if mode:result=ready_batch(q,epoch,1,fixed.items,1,ready_draw,gl_present,fixed.samples,fixed.waits,fixed.stages,C.byref(fixed.completed),ready_poll,None)
  else:result=batch(q,epoch,1,fixed.items,1,raw_draw,gl_present,fixed.samples,fixed.waits,fixed.stages,C.byref(fixed.completed))
  end=time.perf_counter_ns();assert result==1 and fixed.completed.value==1 and fixed.samples[4]==k
  stages=(U*3)();assert gpu.nf_owned_gpu_present_stages(stages)==0
  timing=None;breakdown=None
  if mode:
   t=(U*40)();z=(U*48)();ready_bridge.nf_owned_ready_timing.argtypes=[P];ready_bridge.nf_owned_ready_breakdown.argtypes=[P]
   assert ready_bridge.nf_owned_ready_timing(t)==1 and ready_bridge.nf_owned_ready_breakdown(z)==1;timing=list(t[:5]);breakdown=list(z[:6])
  scene_stages=(U*3)();hud_stages=(U*3)();gpu.nf_owned_gpu_sky_draw_stages.argtypes=[P];gpu.nf_owned_gpu_sky_hud_stages.argtypes=[P]
  assert gpu.nf_owned_gpu_sky_draw_stages(scene_stages)==0 and gpu.nf_owned_gpu_sky_hud_stages(hud_stages)==0
  uploads=(U*3)();callback_profile=(U*4)();gpu.nf_owned_gpu_upload_profile.argtypes=[P];gpu.nf_owned_gpu_callback_profile.argtypes=[P]
  assert gpu.nf_owned_gpu_upload_profile(uploads)==0 and gpu.nf_owned_gpu_callback_profile(callback_profile)==0
  input_stages=(U*4)();gpu.nf_owned_input_stages.argtypes=[P];assert gpu.nf_owned_input_stages(input_stages)==1
  reuse=(U*3)();gpu.nf_owned_gpu_pool_reuse_profile.argtypes=[P];assert gpu.nf_owned_gpu_pool_reuse_profile(reuse)==0
  records.append(dict(pool_reuse_profile=list(reuse),input_stages_ns=list(input_stages),upload_profile=list(uploads),callback_profile=list(callback_profile),scene_stages_ns=list(scene_stages),hud_stages_ns=list(hud_stages),iteration=k,mode=mode,alpha=fixed.items[0].alpha,callback_ms=(end-begin)/1e6,commit_lateness_ms=(fixed.samples[6]-deadline)/1e6,draw_ms=(fixed.draws[0].completed_ns-fixed.draws[0].started_ns)/1e6,present_ms=sum(stages)/1e6,swap_ms=stages[1]/1e6,ready_timing=timing,ready_breakdown=breakdown))
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[-1]
 summary={}
 for mode in (0,1):
  values=sorted(x['commit_lateness_ms'] for x in records if x['mode']==mode);callbacks=sorted(x['present_ms'] for x in records if x['mode']==mode)
  summary[mode]=dict(count=len(values),median_lateness_ms=statistics.median(values),p95_lateness_ms=values[int(.95*len(values))],max_lateness_ms=max(values),over_two_frames=sum(x>1000/30 for x in values),median_present_ms=statistics.median(callbacks),max_present_ms=max(callbacks))
 pool=(U*5)();gpu.nf_owned_gpu_pool_stats.argtypes=[P];assert gpu.nf_owned_gpu_pool_stats(pool)==0 and pool[0]>=600 and all(pool[2:]) and len(set(pool[2:]))==3
 assert adapter.nf_gpu_ready_close()==0
 Path('work/camera/gl-queued-targets-results.json').write_text(json.dumps(dict(records=records,summary=summary,swap_interval=list(observed),final_4k_exact=True,scope='Same-context changing fullscene samples within captured9122->9126 interval, precomputed120 complete owners, ABBA direct/ready nativecommit,600 sequentialsamples; no live producer; shared queue history and client-scaled viewport, not physical4Kscanout or gameplay proof'),indent=2));print('MOVING_READY_VS_DIRECT',summary)
 for index in range(3):
  out=(U*16)();assert probe.nf_dx_bridge_diagnostic(out)==0 and out[9]==1 and out[11]==index+1 and out[10]==0
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[-1]
 checks.append(dict(reopened_presentations=3,foreign_thread_without_context_rejected=rejected,idempotent_close=True))
finally:
 assert probe.nf_dx_bridge_close()==0 and probe.nf_dx_bridge_active()==0
 assert probe.nf_dx_bridge_close()==0
 if q:h.nf_owned_handoff_destroy(q)
 if "adapter" in locals():assert adapter.nf_gpu_ready_close()==0
 assert gpu.nf_owned_gpu_close()
 assert gpu.nf_owned_gpu_target_queries_pending()==0
 cleared=(U*5)();assert gpu.nf_owned_gpu_pool_stats(cleared)==0 and list(cleared)==[0]*5
 fences=(U*4)();gpu.nf_owned_gpu_pool_fences.argtypes=[P];assert gpu.nf_owned_gpu_pool_fences(fences)==0 and fences[0]==fences[1] and fences[2]>0 and fences[3]==0
 Path("work/camera/queued-targets-cleanup.json").write_text(json.dumps(list(fences)))
 ns['prepared'].close();ns['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/dx-native-batch-present-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,interop_checks=interop_checks,scope='Captured9122->9126 reconstructed complete geometry/camera/model motion and recorded-angle ROM-derived sky. Exact4K parity versus existing renderer; not live timing/scanout or independent visual fidelity.'),indent=2));print('PASS complete motion native GPU batch',checks)
