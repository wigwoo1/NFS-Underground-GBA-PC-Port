import sys,json,time
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
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-gpu-segmented-source-candidate.dll').resolve()));bridge=C.CDLL(str((p/'owned-dx-source-diagnostic-bridge.dll').resolve()))
gpu.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];bridge.nf_dx_bridge_diagnostic.argtypes=[C.c_void_p];bridge.nf_dx_window_stats.argtypes=[C.c_void_p]
checks=[];images=[]
try:
 import owned_sampled_world_frame as assembly
 from owned_segmented_frame_candidate import SegmentedFrame
 assembly.join_frame=SegmentedFrame.join
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 assert gpu.nf_owned_gpu_window(0)==0
 rgb=C.create_string_buffer(3840*2160*3)
 assert json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(cached.sample(x['alpha']))) for x in expected]))==expected
 source_cameras=cached.source_cameras
 samples=[cached.sample(x['alpha']) for x in expected];masks=[cached.source_masks[x['alpha']] for x in expected]
 cached.close();prepared.close();gc_mod=__import__('gc');gc_mod.collect()
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=samples[index];offsets,mask,total,_=masks[index]
  owned=OwnedSourceDraw(bytes(frame),camera,models,bounds,detail['geometry_records'],*source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  assert gpu.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;before=rgb.raw;digest=hashlib.sha256(before).hexdigest();images.append(digest)

  import struct,gc
  from owned_segmented_frame_candidate import SegmentedFrame
  from owned_segmented_source_draw_candidate import OwnedSegmentedSourceDraw
  assert isinstance(frame,SegmentedFrame);seg=frame
  segmented=OwnedSegmentedSourceDraw(seg,camera,models,bounds,detail['geometry_records'],*source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  context=segmented.context
  gc.collect()
  gpu.nf_owned_gpu_segmented_source_context_size.restype=C.c_size_t
  gpu.nf_owned_gpu_segmented_source_context_callback.argtypes=[C.c_void_p]
  assert gpu.nf_owned_gpu_segmented_source_context_size()==C.sizeof(context)
  assert gpu.nf_owned_gpu_segmented_source_context_callback(C.byref(context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'Segmented4Kpixels mismatch'
  context.tail_bytes-=1
  assert gpu.nf_owned_gpu_segmented_source_context_callback(C.byref(context))==37
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'Rejected segmented input changed target'
  checks.append(dict(alpha=alpha,sha256=digest,retained_tail_bytes=len(seg.tail),prefix_bytes=len(seg.prefix)))
 assert len(set(images))>1
finally:
 assert gpu.nf_owned_gpu_close()
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
result=dict(result='PASS_SEGMENTED_COMPLETE_SOURCE_4K_PIXELS',checks=checks,pixels_per_frame=8294400,scope='Five truly segmented preparation samples exact complete signatures and4KRGB after preparation closes and GC; source owners retain prefix/tail without materialization for segmented draw; malformedtailrejected. Diagnosticreadbacks,notlivecadence/physicalscanoutproof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result)
