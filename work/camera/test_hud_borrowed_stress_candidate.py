import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
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
reference=json.loads(Path('work/camera/prototype-runs/hud-borrowed-queue-baseline-20261009.json').read_text())['samples']
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
original_cdll=C.CDLL
def selected_load(path,*args,**kwargs):
 if Path(path).name.startswith('owned-gpu-source-'):
  path=str(Path(path).with_name('owned-gpu-hud-borrowed-rows-candidate.dll'))
 return original_cdll(path,*args,**kwargs)
C.CDLL=selected_load
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);worker=NativeSourceWorker();results=[]

import struct
from owned_segmented_frame_candidate import SegmentedFrame
library=C.CDLL(str((Path('work/camera')/'owned-gpu-source-hud-cache-lease-candidate.dll').resolve()))
records=[]
try:
 for index in range(30):
  ref_index=index%5;alpha=expected[ref_index]['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  # New immutable owner each iteration forces actual creator-cache eviction.
  epoch=1+(index//3)%2;prefix=bytearray(frame.prefix);base=bytearray(frame.base);struct.pack_into('<Q',prefix,24,epoch);struct.pack_into('<Q',base,24,epoch)
  changed=SegmentedFrame(bytes(prefix),bytes(base),frame.tail_offset)
  fallback=index%5==4;draw_frame=changed.materialize() if fallback else changed
  owned=OwnedSourceDraw(draw_frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  row=worker.prepare(owned,epoch,1,index,True).result(20);assert row['native_rgb_sha256']==reference[ref_index]['rgb_sha256']
  stats=(C.c_uint64*3)();cache=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats) and library.nf_hud_cache_lease_stats(cache)
  assert stats[0]<=2 and stats[1]<=11182080 and stats[2]==stats[0]+(0 if fallback else 1),list(stats)
  assert (cache[0]==0 and cache[1]==0) if fallback else (cache[0]!=0 and cache[1]==epoch),list(cache)
  try:worker.present(epoch+1,1,index).result(20)
  except NativeFrameIdentityError:pass
  else:raise AssertionError('Wrong epoch pending frame accepted')
  worker.abort(epoch,1,index).result(20)
  records.append(dict(epoch=epoch,fallback=fallback,rgb_sha256=row['native_rgb_sha256'],owners=list(stats),cache=list(cache)))
finally:worker.close();cached.close();history.close()
assert not worker.thread.is_alive() and worker.error is None
stats=(C.c_uint64*3)();cache=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats) and list(stats)==[0,0,0];assert library.nf_hud_cache_lease_stats(cache) and cache[0]==cache[1]==0
assert cache[2]==6*5591040,cache[2]
out=dict(result='PASS_QUEUED_HUD_CACHE_EVICTION_EPOCH_FALLBACK',draws=len(records),wrong_epoch_rejections=30,fallback_draws=6,fallback_cache_copy_bytes=cache[2],final_owners=list(stats),records=records,scope='Captured5image cycle with synthetic header epoch transitions/newimmutableowners, realqueued renderer authority and six contiguousfallback draws. No live trajectory/cadence claim.')
Path('work/camera/prototype-runs/hud-borrowed-stress-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
