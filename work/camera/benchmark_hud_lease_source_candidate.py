import owned_segmented_display_placement_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import sys,json,ctypes as C,weakref
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
reference=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples']
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);from owned_native_source_hud_lease_session_candidate import NativeSourceSession

import time,statistics,hashlib,numpy as np
from owned_native_source_segmented_session_candidate import NativeSourceSession as Baseline
import owned_native_source_hud_lease_session_candidate as candidate_module
candidate_module.OwnedD3DConsumer=__import__('owned_native_source_segmented_session_candidate').OwnedD3DConsumer
Candidate=candidate_module.NativeSourceSession
owners=[]
for item in expected:
 alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
 owners.append(OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha)))
trials=[]
try:
 for trial in range(4):
  pair={}
  for name in (('baseline','lease') if trial%2==0 else ('lease','baseline')):
   session=(Baseline if name=='baseline' else Candidate)();cost=[];total=[];cold=None
   if name=='lease':
    session.source.nf_hud_authority_reuses.restype=C.c_uint64;before=session.source.nf_hud_authority_reuses()
   try:
    for repeat in range(6):
     for index,owned in enumerate(owners):
      start=time.perf_counter_ns();row=session.prepare(owned,1,1,repeat*5+index);elapsed=time.perf_counter_ns()-start
      if repeat==0:
       if index==0:cold=dict(source_ms=row['source_prepare_ns']/1e6,complete_prepare_ms=elapsed/1e6)
       rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
       rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];assert hashlib.sha256(rgb.tobytes()).hexdigest()==reference[index]['rgb_sha256']
      else:cost.append(row['source_prepare_ns']);total.append(elapsed)
      session.abort(1,1,repeat*5+index)
    pair[name]=dict(samples=len(cost),median_source_ms=statistics.median(cost)/1e6,max_source_ms=max(cost)/1e6,median_complete_prepare_ms=statistics.median(total)/1e6,cold_first=cold)
    if name=='lease':
     pair[name]['authority_reuses']=session.source.nf_hud_authority_reuses()-before;assert pair[name]['authority_reuses']>=25
   finally:session.close()
   if name=='lease':
    stats=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(stats) and list(stats)==[0,0,0]
  trials.append(pair)
finally:cached.close();history.close()
out=dict(result='MATCHED_SEGMENTED_HUD_LEASE_CALLBACK_COST',trials=trials,median_trial_source_ms={k:statistics.median(t[k]['median_source_ms'] for t in trials) for k in ('baseline','lease')},median_trial_complete_prepare_ms={k:statistics.median(t[k]['median_complete_prepare_ms'] for t in trials) for k in ('baseline','lease')},scope='Four alternating renderer pairs; same five captured segmented frames, exact4Kfirstcycle hashes,25warmcallbacks eachsession plus cold first. Completeprepare includes native consumer render. Static capturedinterval not live whole-game/cadence proof.')
Path('work/camera/prototype-runs/hud-lease-matched-cost-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
