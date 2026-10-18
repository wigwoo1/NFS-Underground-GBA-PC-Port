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
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
session=NativeSourceSession();results=[]

try:
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  row=session.prepare(owned,1,1,index);rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  import numpy as np,hashlib
  rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];digest=hashlib.sha256(rgb.tobytes()).hexdigest();assert digest==reference[index]['rgb_sha256']
  snapshot=next(x for x in session.hud_snapshots if x._base is frame.base);stats=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(stats);assert stats[2]==stats[0]+1,list(stats)
  # Invalid association rejected before accepting a frame; leases must be balanced.
  for tail,token,epoch,prefix in [(owned.tail_pointer+1,snapshot.token,snapshot.epoch,owned.prefix_bytes),(owned.tail_pointer,snapshot.token+1000,snapshot.epoch,owned.prefix_bytes),(owned.tail_pointer,snapshot.token,snapshot.epoch+1,owned.prefix_bytes),(owned.tail_pointer,snapshot.token,snapshot.epoch,owned.prefix_bytes+1)]:
   assert session.source.nf_owned_gpu_source_segmented_hud_callback(C.byref(owned.context),prefix,tail,owned.tail_bytes,token,epoch)==37
   after=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(after)
   assert list(after)==(list(stats) if prefix==owned.prefix_bytes else [stats[0],stats[1],stats[0]]),list(after)
  session.abort(1,1,index)
  session.prepare(owned,1,1,index+100);session.abort(1,1,index+100)
  session.prepare(owned,1,1,index+200)
  assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  fast_rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];assert hashlib.sha256(fast_rgb.tobytes()).hexdigest()==digest
  session.abort(1,1,index+200)
  # Drop all creator refs while native cache alone retains the immutable bytes.
  for creator in session.hud_snapshots:creator.close()
  session.hud_snapshots=[]
  held=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(held) and list(held)==[1,5591040,1],list(held)
  # Replacement snapshot must transfer the native cache ref and release the old one.
  session.prepare(owned,1,1,index+300);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  assert hashlib.sha256(np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3].tobytes()).hexdigest()==digest
  session.abort(1,1,index+300)
  after=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(after) and list(after)==[1,5591040,2],list(after)
  cache=(C.c_uint64*3)();assert session.source.nf_hud_cache_lease_stats(cache) and cache[0]!=0 and cache[2]==0,list(cache)
  results.append(dict(alpha=alpha,rgb_sha256=digest,source_prepare_ns=row['source_prepare_ns']))
finally:session.close();cached.close();history.close()
stats=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(stats) and list(stats)==[0,0,0]
session.source.nf_hud_authority_reuses.restype=C.c_uint64;reuses=session.source.nf_hud_authority_reuses();assert reuses>=5
out=dict(result='PASS_NATIVE_HUD_CACHE_LEASE_4K_LIFETIME',samples=results,association_rejections=20,authority_reuses=reuses,final_stats=list(stats),scope='Five captured fullscene4K images and native wrong-source/token/epoch/prefix rejection with balanced leases. Synchronous component integration only, not live pause/cadence/fullgame proof.')
Path('work/camera/prototype-runs/hud-cache-lease-lifetime-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
