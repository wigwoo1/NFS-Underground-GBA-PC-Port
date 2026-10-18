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
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-gpu-playable-input-profile-candidate.dll').resolve()));bridge=C.CDLL(str((p/'owned-dx-source-ready-candidate.dll').resolve()))
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
   if ready:break
   assert time.perf_counter()-wait_start<2,'Display availability timed out before source draw'
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  assert gpu.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;before=rgb.raw;digest=hashlib.sha256(before).hexdigest();images.append(digest)
  values=(C.c_uint64*16)();status=bridge.nf_dx_bridge_diagnostic(values)
  assert status==0 and values[9]==1 and values[14]==0,(status,list(values))
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'Source target changed by DXGI presentation'
  bridge.nf_dx_availability_poll.argtypes=[C.c_uint];assert bridge.nf_dx_availability_poll(3)==-45;# Do not consume the next frame's availability signal after presentation.
  config=(C.c_uint64*7)();bridge.nf_dx_availability_stats.argtypes=[C.c_void_p];assert bridge.nf_dx_availability_stats(config)==0 and list(config)==[0,0,0,1,1,1,0],list(config)
  statsrow=(C.c_uint64*10)();bridge.nf_dx_display_stats.argtypes=[C.c_void_p];assert bridge.nf_dx_display_stats(statsrow)==0
  checks.append(dict(availability_before_draw=True,availability_polls=polls,availability_stats=list(config),display_stats=list(statsrow),alpha=alpha,rgba_bytes_exact_flipped=values[7],row_pitch=values[6],source_rgb_sha256=digest,values=list(values)))
  creation=(C.c_uint64*5)();bridge.nf_dx_creation_diagnostic.argtypes=[C.c_void_p];assert bridge.nf_dx_creation_diagnostic(creation)==0
  user=C.WinDLL('user32',use_last_error=True);user.GetParent.argtypes=[C.c_void_p];user.GetParent.restype=C.c_void_p;user.MoveWindow.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_int,C.c_int];user.GetClientRect.argtypes=[C.c_void_p,C.c_void_p]
  child=creation[1];parent=user.GetParent(child);assert parent
  if index==1:assert user.MoveWindow(parent,0,0,1000,700,0)
  if index>=2:
   child_rect=(C.c_long*4)();parent_rect=(C.c_long*4)();assert user.GetClientRect(child,child_rect) and user.GetClientRect(parent,parent_rect);assert list(child_rect)==list(parent_rect),'DXGI child did not follow parent resize'

 assert len(set(images))>1,'Moving full scene produced identical pixels'
finally:
 assert bridge.nf_dx_bridge_close()==0
 stats=(C.c_uint64*4)();assert bridge.nf_dx_window_stats(stats)==0;print('window cleanup',list(stats));assert stats[0]==stats[1] and stats[3]==0
 config=(C.c_uint64*7)();assert bridge.nf_dx_availability_stats(config)==0 and list(config)==[0,0,0,1,1,1,1],list(config)
 assert bridge.nf_dx_availability_poll(0)==-45
 assert gpu.nf_owned_gpu_close()
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
result=dict(result='PASS_COMPLETE_SOURCE_SKY_HUD_DXGI_4K_PIXELS',checks=checks,pixels_per_frame=8294400,window_stats=list(stats),initialization_stats=list(initial_stats),scope='Initialization produced zero presents/readbacks, then availability was awaited before every source draw including first. Five actual captured source samples with source cameras/masks and actual playable crossfade sky/HUD: all4K RGBA bytes copied to DXGI backbuffer match vertically corrected GL target, source target unchanged and window cleanup balanced. Resize counter zero: active resize coverage unproven. Diagnostic readbacks only; no physical scanout, independent visual fidelity or live cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})






