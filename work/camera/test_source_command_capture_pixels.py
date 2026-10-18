import sys,json,time,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import ctypes as C,hashlib
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-gpu-source-command-capture-candidate.dll').resolve()));bridge=C.CDLL(str((p/'owned-dx-source-completion-probe-candidate.dll').resolve()))
gpu.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];bridge.nf_dx_bridge_diagnostic.argtypes=[C.c_void_p];bridge.nf_dx_window_stats.argtypes=[C.c_void_p]
checks=[];images=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 assert gpu.nf_command_capture_open()==0
 assert gpu.nf_owned_gpu_window(0)==0
 initial=(C.c_uint64*16)();bridge.nf_dx_bridge_initialize.argtypes=[C.c_void_p]
 assert bridge.nf_dx_bridge_initialize(initial)==0 and initial[11]==0 and initial[14]==0,list(initial)
 initial_stats=(C.c_uint64*4)();bridge.nf_dx_bridge_stats.argtypes=[C.c_void_p]
 assert bridge.nf_dx_bridge_stats(initial_stats)==0 and list(initial_stats)==[0,0,0,1],list(initial_stats)
 assert bridge.nf_dx_bridge_initialize(initial)==0 and initial[11]==0,'Repeated initialization presented a frame'
 foreign=[]
 def foreign_poll():foreign.append(bridge.nf_dx_availability_poll(0))
 thread=threading.Thread(target=foreign_poll);thread.start();thread.join();assert foreign==[-45],foreign
 rgb=C.create_string_buffer(3840*2160*3)
 for index,item in enumerate(expected):
  bridge.nf_dx_availability_poll.argtypes=[C.c_uint]
  wait_start=time.perf_counter();polls=0
  while True:
   ready=bridge.nf_dx_availability_poll(2);polls+=1
   assert ready in (0,1),ready
   if ready:
    assert bridge.nf_dx_availability_poll(0)==1 and bridge.nf_dx_availability_poll(0)==1,'Ready permission lost without presentation'
    break
   assert time.perf_counter()-wait_start<2,'Display availability timed out before source draw'
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  assert gpu.nf_command_capture_mark(1,1,index)==0
  assert gpu.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;before=rgb.raw;digest=hashlib.sha256(before).hexdigest();images.append(digest)
  values=(C.c_uint64*16)();bridge.nf_dx_prepare.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint,C.c_void_p]
  bridge.nf_dx_present_prepared.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p]
  bridge.nf_dx_abort_prepared.argtypes=[C.c_uint64,C.c_uint64,C.c_uint64]
  status=bridge.nf_dx_prepare(1,1,index,1,values)
  assert status==0 and values[9]==1 and values[14]==0,(status,list(values))
  prepared_values=list(values)
  assert values[11]==index,'Preparation unexpectedly presented'
  assert bridge.nf_dx_present_prepared(1,2,index,values)==51
  assert bridge.nf_dx_prepare(1,1,index,0,values)==51
  assert bridge.nf_dx_bridge_diagnostic(values)==51
  assert bridge.nf_dx_bridge_present_callback(None)==0
  assert bridge.nf_dx_abort_prepared(1,2,index)==51
  if index==2:
   assert bridge.nf_dx_abort_prepared(1,1,index)==0
   assert bridge.nf_dx_present_prepared(1,1,index,values)==51
   assert bridge.nf_dx_prepare(1,1,index,1,values)==0 and values[9]==1
  assert bridge.nf_dx_present_prepared(1,1,index,values)==0 and values[11]==index+1
  assert bridge.nf_dx_present_prepared(1,1,index,values)==51
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'Source target changed by DXGI presentation'
  bridge.nf_dx_availability_poll.argtypes=[C.c_uint];assert bridge.nf_dx_availability_poll(3)==-45;# Do not consume the next frame's availability signal after presentation.
  config=(C.c_uint64*7)();bridge.nf_dx_availability_stats.argtypes=[C.c_void_p];assert bridge.nf_dx_availability_stats(config)==0 and list(config)==[0,0,0,2,2,1,0],list(config)
  statsrow=(C.c_uint64*10)();bridge.nf_dx_display_stats.argtypes=[C.c_void_p];assert bridge.nf_dx_display_stats(statsrow)==0
  checks.append(dict(availability_before_draw=True,availability_polls=polls,availability_stats=list(config),display_stats=list(statsrow),alpha=alpha,rgba_bytes_exact_flipped=prepared_values[7],row_pitch=prepared_values[6],source_rgb_sha256=digest,prepared_values=prepared_values,present_values=list(values)))
  creation=(C.c_uint64*5)();bridge.nf_dx_creation_diagnostic.argtypes=[C.c_void_p];assert bridge.nf_dx_creation_diagnostic(creation)==0
  user=C.WinDLL('user32',use_last_error=True);user.GetParent.argtypes=[C.c_void_p];user.GetParent.restype=C.c_void_p;user.MoveWindow.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_int,C.c_int];user.GetClientRect.argtypes=[C.c_void_p,C.c_void_p]
  child=creation[1];parent=user.GetParent(child);assert parent
  if index==1:assert user.MoveWindow(parent,0,0,1000,700,0)
  if index>=2:
   child_rect=(C.c_long*4)();parent_rect=(C.c_long*4)();assert user.GetClientRect(child,child_rect) and user.GetClientRect(parent,parent_rect);assert list(child_rect)==list(parent_rect),'DXGI child did not follow parent resize'

 class Context(C.Structure):_fields_=[('epoch',C.c_uint64),('timed',C.c_uint32),('result',C.c_int32),('elapsed',C.c_uint64)]
 bridge.nf_dx_prepare_callback.argtypes=[C.c_uint64]*3;bridge.nf_dx_present_prepared_callback.argtypes=[C.c_uint64]*3+[C.c_void_p]
 assert bridge.nf_dx_prepare_callback(1,9,98)==0
 ctx=Context(2,1,0,0);assert bridge.nf_dx_present_prepared_callback(1,9,98,C.byref(ctx))==0
 ctx=Context(1,1,99,0);assert bridge.nf_dx_present_prepared_callback(1,9,98,C.byref(ctx))==1 and ctx.result==0 and ctx.elapsed>0
 completion=(C.c_uint64*15)();bridge.nf_dx_completion_read.argtypes=[C.c_uint,C.c_void_p]
 assert bridge.nf_dx_completion_count()==1 and bridge.nf_dx_completion_dropped()==0 and bridge.nf_dx_completion_read(0,completion)==0
 assert list(completion[:3])==[1,9,98] and completion[7]==completion[8]==2 and completion[13]==completion[14]==0
 assert all(x in (0x911a,0x911b,0x911c) for x in completion[3:7]),list(completion)
 assert bridge.nf_dx_prepare_count()==1 and bridge.nf_dx_prepare_dropped()==0 and bridge.nf_dx_phase_count()==1
 prep=(C.c_uint64*21)();phase=(C.c_uint64*18)();bridge.nf_dx_prepare_read.argtypes=[C.c_uint,C.c_void_p];bridge.nf_dx_phase_read.argtypes=[C.c_uint,C.c_void_p]
 assert bridge.nf_dx_prepare_read(0,prep)==0 and list(prep[:3])==[1,9,98] and prep[19]==0
 assert bridge.nf_dx_phase_read(0,phase)==0 and phase[16]==0
 assert list(prep[3:11])==sorted(prep[3:11]) and list(phase[:8])==sorted(phase[:8]) and prep[10]<=phase[0]
 observations=[];bridge.nf_dx_observation_read.argtypes=[C.c_uint,C.c_void_p]
 assert bridge.nf_dx_observation_count()==3 and bridge.nf_dx_observation_dropped()==0
 for i in range(3):
  observation=(C.c_uint64*16)();assert bridge.nf_dx_observation_read(i,observation)==0
  assert list(observation[:4])==[1,9,98,i] and observation[4]<=observation[5] and observation[6]>0
  assert observation[7]==(5 if i<2 else 6) and observation[8]==0 and observation[9]==observation[7]
  observations.append(list(observation))
 assert bridge.nf_dx_prepare(1,9,99,0,(C.c_uint64*16)())==0,'Pending frame for close cleanup'
 assert len(set(images))>1,'Moving full scene produced identical pixels'
finally:
 assert bridge.nf_dx_bridge_close()==0
 stats=(C.c_uint64*4)();assert bridge.nf_dx_window_stats(stats)==0;print('window cleanup',list(stats));assert stats[0]==stats[1] and stats[3]==0
 config=(C.c_uint64*7)();assert bridge.nf_dx_availability_stats(config)==0 and list(config)==[0,0,0,2,2,1,1],list(config)
 assert bridge.nf_dx_availability_poll(0)==-45
 statscmd=(C.c_uint64*5)();gpu.nf_command_capture_stats.argtypes=[C.c_void_p];assert gpu.nf_command_capture_stats(statscmd)==0 and statscmd[2]==0 and statscmd[4]==120
 capture_stats=list(statscmd)
 rec=C.create_string_buffer(statscmd[0]*statscmd[4]);payload=C.create_string_buffer(statscmd[1]);gpu.nf_command_capture_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
 assert gpu.nf_command_capture_copy(rec,len(rec),payload,len(payload))==0
 baseline=json.loads(Path('work/camera/prototype-runs/source-gpu-timestamp-component.json').read_text());assert images==[x['source_rgb_sha256'] for x in baseline['checks']],'Capture changed baseline scene pixels'
 import struct,collections
 decoded=list(struct.iter_unpack('<II12dQQ',rec.raw));assert len(decoded)==statscmd[0]
 assert [list(x[2:5]) for x in decoded if x[0]==1]==[[1,1,i] for i in range(5)]
 assert all(x[-2]+x[-1]<=len(payload) for x in decoded)
 counts=dict(collections.Counter(x[0] for x in decoded));assert counts[10]>0 and counts[12]>0 and counts[100]>0
 Path('work/camera/prototype-runs/source-command-records.bin').write_bytes(rec.raw);Path('work/camera/prototype-runs/source-command-payload.bin').write_bytes(payload.raw)
 gpu.nf_command_capture_close();assert gpu.nf_command_capture_stats(statscmd)==0 and statscmd[0]==statscmd[1]==0
 assert gpu.nf_owned_gpu_close()
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
result=dict(command_counts=counts,capture_stats=capture_stats,capture_scope='Initial command stream, not complete replay: dynamic shader/program/active texture and texture lifetime require explicit recording before D3D parity can be claimed.',result='PASS_COMPLETE_SOURCE_SKY_HUD_DXGI_4K_PIXELS',checks=checks,pixels_per_frame=8294400,window_stats=list(stats),initialization_stats=list(initial_stats),completion_probe=list(completion),observations=observations,adapter_prepare_trace=list(prep),adapter_present_trace=list(phase),adapter_elapsed_ns=ctx.elapsed,prepared_identity_checks=True,pending_close_cleanup=True,scope='Split preparation performs transfer without presenting; matched identity presents once, mismatches/duplicates reject and abort permits replacement. Initialization produced zero presents/readbacks, then availability was awaited before every source draw including first. Five actual captured source samples with source cameras/masks and actual playable crossfade sky/HUD: all4K RGBA bytes copied to DXGI backbuffer match vertically corrected GL target, source target unchanged and window cleanup balanced. Window resize counter recorded; no live resize/cadence certification. Diagnostic readbacks only; no physical scanout, independent visual fidelity or live cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})







