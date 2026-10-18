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
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-gpu-source-no-upload-candidate.dll').resolve()));bridge=C.CDLL(str((p/'owned-dx-source-completion-probe-candidate.dll').resolve()))
gpu.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];bridge.nf_dx_bridge_diagnostic.argtypes=[C.c_void_p];bridge.nf_dx_window_stats.argtypes=[C.c_void_p]
present_results=[];consumer=None;consumer_stats=None;packet_checks=[];checks=[];images=[];gpu.nf_source_packets_stats.argtypes=[C.c_void_p];gpu.nf_source_packets_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
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
  gpu.nf_source_packets_begin.argtypes=[C.c_uint64]*3;gpu.nf_source_packets_identity.argtypes=[C.c_void_p]
  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,1,index)==0;assert gpu.nf_source_packets_begin(1,1,index)==1
  identity=(C.c_uint64*3)();assert gpu.nf_source_packets_identity(identity)==0 and list(identity)==[1,1,index]
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
  assert gpu.nf_command_capture_end_frame(1,1,index)==0
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
  gpu.nf_source_packets_publish.argtypes=[C.c_void_p];publication=(C.c_uint64*7)();assert gpu.nf_source_packets_publish(publication)==0 and list(publication[:3])==[1,1,index];assert gpu.nf_source_packets_publish(publication)==1
  packet_stats=(C.c_uint*3)();assert gpu.nf_source_packets_stats(packet_stats)==0;nv,nd,overflow=packet_stats;assert nv>0 and nd>0 and overflow==0
  owned_vertices=C.create_string_buffer(nv*80);owned_offsets=(C.c_uint*(nd+1))();assert gpu.nf_source_packets_copy(owned_vertices,len(owned_vertices),owned_offsets,C.sizeof(owned_offsets))==0
  import struct,math
  assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<d',owned_vertices.raw));assert owned_offsets[0]==0 and owned_offsets[-1]==nv and all((owned_offsets[j+1]-owned_offsets[j])%3==0 for j in range(nd))
  gpu.nf_source_texture_stats.argtypes=[C.c_void_p];gpu.nf_source_texture_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
  ts=(C.c_uint*2)();assert gpu.nf_source_texture_stats(ts)==0;nt,nb=ts;assert nt>0 and nb>0
  tb=C.create_string_buffer(nb);tr=(C.c_uint*(nt*4))();di=(C.c_uint*nd)();assert gpu.nf_source_texture_copy(tb,nb,tr,C.sizeof(tr),di,C.sizeof(di))==0
  assert all(1<=x<=nt for x in di);assert all(tr[j*4+3]==tr[j*4]*tr[j*4+1]*4 and tr[j*4+2]+tr[j*4+3]<=nb for j in range(nt))
  gpu.nf_source_clip_copy.argtypes=[C.c_void_p,C.c_size_t];clips=(C.c_int*(nd*4))();assert gpu.nf_source_clip_copy(clips,C.sizeof(clips))==0
  assert all(0<=clips[j*4]<=clips[j*4+2]<=3840 and 0<=clips[j*4+1]<=clips[j*4+3]<=2160 for j in range(nd))
  gpu.nf_source_state_copy.argtypes=[C.c_void_p,C.c_size_t];states=C.create_string_buffer(nd*72);assert gpu.nf_source_state_copy(states,len(states))==0;Path(f'work/camera/prototype-runs/source-owned-state-{index}.bin').write_bytes(states.raw)
  gpu.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p];gpu.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];sky_valid=(C.c_uint*2)();sky_weights=(C.c_double*2)();assert gpu.nf_source_sky_info(sky_valid,sky_weights)==0 and sky_valid[0]==1 and sky_weights[0]==1
  sky_hashes=[]
  for slot in range(2):
   if sky_valid[slot]:
    sky_bytes=C.create_string_buffer(153600);assert gpu.nf_source_sky_copy(slot,sky_bytes,len(sky_bytes))==0;sky_hashes.append(hashlib.sha256(sky_bytes.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-sky-{index}-{slot}.rgba').write_bytes(sky_bytes.raw)
    assert 0<=sky_weights[slot]<=1
  gpu.nf_source_hud_planes_info.argtypes=[C.c_void_p];gpu.nf_source_hud_plane_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];hud_info=(C.c_uint*2)();assert gpu.nf_source_hud_planes_info(hud_info)==0 and hud_info[0]==1
  hud_hashes=[]
  for plane in range(3):
   hb=C.create_string_buffer(153600);assert gpu.nf_source_hud_plane_copy(plane,hb,len(hb))==0;hud_hashes.append(hashlib.sha256(hb.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-hud-{index}-{plane}.rgba').write_bytes(hb.raw)
  count=gpu.nf_source_hud_batches_count();assert 0<count<=160;gpu.nf_source_hud_batches_copy.argtypes=[C.c_void_p,C.c_size_t];batch=C.create_string_buffer(count*112);assert gpu.nf_source_hud_batches_copy(batch,len(batch))==0;Path(f'work/camera/prototype-runs/source-owned-hud-batches-{index}.bin').write_bytes(batch.raw)
  packet_checks.append(dict(hud_batches=count,hud_batch_sha256=hashlib.sha256(batch.raw).hexdigest(),hud_info=list(hud_info),hud_hashes=hud_hashes,sky_valid=list(sky_valid),sky_weights=list(sky_weights),sky_hashes=sky_hashes,state_sha256=hashlib.sha256(states.raw).hexdigest(),clip_sha256=hashlib.sha256(bytes(clips)).hexdigest(),texture_count=nt,texture_bytes=nb,texture_sha256=hashlib.sha256(tb.raw).hexdigest(),frame=index,vertices=nv,draws=nd,overflow=overflow,sha256=hashlib.sha256(owned_vertices.raw).hexdigest()));Path(f'work/camera/prototype-runs/source-owned-vertices-{index}.bin').write_bytes(owned_vertices.raw)
  gpu.nf_source_backdrop_copy.argtypes=[C.c_void_p,C.c_size_t];backdrop=C.create_string_buffer(640)
  assert gpu.nf_source_backdrop_copy(backdrop,639)==1
  assert gpu.nf_source_backdrop_copy(backdrop,640)==0
  import concurrent.futures
  with concurrent.futures.ThreadPoolExecutor(1) as worker:assert worker.submit(gpu.nf_source_backdrop_copy,backdrop,640).result()==1
  assert gpu.nf_source_packets_reset()==1
  Path(f'work/camera/prototype-runs/source-owned-backdrop-{index}.rgba').write_bytes(backdrop.raw)
  packet_checks[-1]['backdrop_sha256']=hashlib.sha256(backdrop.raw).hexdigest();packet_checks[-1]['backdrop_copy_guards']=True
  from owned_source_d3d_present_consumer_candidate import OwnedD3DConsumer
  import numpy as np
  if consumer is None:consumer=OwnedD3DConsumer();consumer.bind_window()
  assert consumer.render(gpu,readback=False) is None
  present_results.append(consumer.present())
  native=consumer.render(gpu)
  import zlib
  ref=np.frombuffer(zlib.decompress(Path(f'work/camera/prototype-runs/gl-source-full-{index}.rgb.z').read_bytes()),np.uint8).reshape(2160,3840,3);packet_checks[-1]['d3d_different_pixels']=int(np.any(native!=ref,axis=2).sum());packet_checks[-1]['d3d_rgb_sha256']=hashlib.sha256(native.tobytes()).hexdigest()
  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,2,index)==0;assert gpu.nf_source_backdrop_copy(backdrop,640)==1
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
 assert len(set(images))==1,'Disabled scene raster changed target pixels'
finally:
 if consumer is not None:
  counter=(C.c_uint64*4)();assert consumer.d.nf_d3d_stats(counter)==0;consumer_stats=list(counter);assert consumer_stats[3]==1
  consumer.close();assert consumer.d.nf_d3d_stats(counter)==0 and counter[2]==counter[3]==0
 assert bridge.nf_dx_bridge_close()==0
 stats=(C.c_uint64*4)();assert bridge.nf_dx_window_stats(stats)==0;print('window cleanup',list(stats));assert stats[0]==stats[1] and stats[3]==0
 config=(C.c_uint64*7)();assert bridge.nf_dx_availability_stats(config)==0 and list(config)==[0,0,0,2,2,1,1],list(config)
 assert bridge.nf_dx_availability_poll(0)==-45
 assert gpu.nf_owned_gpu_close()
 statscmd=(C.c_uint64*5)();gpu.nf_command_capture_stats.argtypes=[C.c_void_p];assert gpu.nf_command_capture_stats(statscmd)==0 and statscmd[2]==0 and statscmd[4]==120
 capture_stats=list(statscmd)
 rec=C.create_string_buffer(statscmd[0]*statscmd[4]);payload=C.create_string_buffer(statscmd[1]);gpu.nf_command_capture_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
 assert gpu.nf_command_capture_copy(rec,len(rec),payload,len(payload))==0
 baseline=json.loads(Path('work/camera/prototype-runs/source-gpu-timestamp-component.json').read_text());assert images!=[x['source_rgb_sha256'] for x in baseline['checks']],'Disabled raster unexpectedly produced complete scene'
 import struct,collections
 decoded=list(struct.iter_unpack('<II12dQQ',rec.raw));assert len(decoded)==statscmd[0]
 assert [list(x[2:5]) for x in decoded if x[0]==1]==[[1,1,i] for i in range(5)]
 assert all(x[-2]+x[-1]<=len(payload) for x in decoded)
 counts=dict(collections.Counter(x[0] for x in decoded));assert counts[10]>0 and counts[12]>0 and counts[100]>0
 print("captured opcodes",counts)
 assert all(counts.get(x,0)>0 for x in [110,111,200,201,202,203,204,205,206,207,208,210,211,212])
 Path('work/camera/prototype-runs/source-hud-batches-records.bin').write_bytes(rec.raw);Path('work/camera/prototype-runs/source-hud-batches-payload.bin').write_bytes(payload.raw)
 gpu.nf_command_capture_close();assert gpu.nf_command_capture_stats(statscmd)==0 and statscmd[0]==statscmd[1]==0
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
result=dict(source_packet_checks=packet_checks,command_counts=counts,capture_stats=capture_stats,capture_scope='Initial command stream, not complete replay: Shader source/program/uniform/texture lifetime now recorded; no faithful replay or D3D parity yet, framebuffer/context objects and validation remain dependencies.',result='PASS_COMPLETE_SOURCE_SKY_HUD_DXGI_4K_PIXELS',checks=checks,pixels_per_frame=8294400,window_stats=list(stats),initialization_stats=list(initial_stats),completion_probe=list(completion),observations=observations,adapter_prepare_trace=list(prep),adapter_present_trace=list(phase),adapter_elapsed_ns=ctx.elapsed,prepared_identity_checks=True,pending_close_cleanup=True,scope='Split preparation performs transfer without presenting; matched identity presents once, mismatches/duplicates reject and abort permits replacement. Initialization produced zero presents/readbacks, then availability was awaited before every source draw including first. Five actual captured source samples with source cameras/masks and actual playable crossfade sky/HUD: all4K RGBA bytes copied to DXGI backbuffer match vertically corrected GL target, source target unchanged and window cleanup balanced. Window resize counter recorded; no live resize/cadence certification. Diagnostic readbacks only; no physical scanout, independent visual fidelity or live cadence proof.')
result['source_renderer_validation']=result['result'];result['result']='PASS_OWNED_D3D_COMPLETE_FRAME_PARITY' if all(x['d3d_different_pixels']==0 for x in packet_checks) else 'OWNED_SOURCE_D3D_FULL_SCENE_PARITY_INCOMPLETE'
gpu.nf_source_suppressed_raster_calls.restype=C.c_uint64;result['suppressed_raster_calls']=gpu.nf_source_suppressed_raster_calls();assert result['suppressed_raster_calls']>0
reference=json.loads(Path('work/camera/prototype-runs/source-sealed-full-component.json').read_text());assert [x['d3d_rgb_sha256'] for x in packet_checks]==[x['d3d_rgb_sha256'] for x in reference['source_packet_checks']]
result['source_renderer_validation']='GL_RASTER_DISABLED_SOURCE_PACKETS_D3D_OUTPUT_UNCHANGED';result['scope']='Scene glBegin/glEnd/glVertex calls suppressed; GL context, state, texture uploads and diagnostic transfer remain. Five native D3D hashes match prior producer exactly. Not GL-independent initialization or live cadence proof.'
gpu.nf_source_suppressed_upload_calls.restype=C.c_uint64;result['suppressed_upload_calls']=gpu.nf_source_suppressed_upload_calls();assert result['suppressed_upload_calls']>0
result['scope']='Source pixel uploads and background subcopy suppressed along with scene rasterization. GL context/empty target allocation/state/diagnostic transfer still remain. Native D3D five output hashes unchanged; not live cadence proof.'
result['persistent_consumer_stats_before_close']=consumer_stats;result['native_frames_without_readback']=5;result['native_frames_with_diagnostic_readback']=5;result['scope']='One native D3D device across five source publications, each consumed once without readback and once with diagnostic verification. All five native hashes unchanged; GL scaffolding/diagnostic source transfer remain. No live presentation or cadence proof.'
result['direct_presentation_results']=present_results;result['scope']='Persistent direct source-owned native consumer: draw without readback, same-device flip present, separate diagnostic draw/readback. GL scene raster/uploads disabled but source scaffolding remains. Occluded status is not visible presentation or cadence proof.'
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})








