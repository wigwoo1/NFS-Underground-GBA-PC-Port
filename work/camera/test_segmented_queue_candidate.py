import sys,json,ctypes as C,weakref
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_worker_candidate import NativeSourceWorker
from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
reference=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples']
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);worker=NativeSourceWorker();results=[]
try:
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  row=worker.prepare(owned,1,1,index*2,True).result(20);assert row['native_rgb_sha256']==reference[index]['rgb_sha256']
  for future in (worker.prepare(owned,1,1,index*2),worker.present(1,1,index*2+1),worker.abort(1,2,index*2)):
   try:future.result(20)
   except NativeFrameIdentityError:pass
   else:raise AssertionError('Wrong pending identity accepted')
  worker.abort(1,1,index*2).result(20)
  worker.prepare(owned,1,1,index*2+1).result(20);worker.present(1,1,index*2+1).result(20)
  results.append(dict(alpha=alpha,rgb_sha256=row['native_rgb_sha256']))
finally:worker.close();cached.close();history.close()
assert not worker.thread.is_alive() and worker.error is None
out=dict(result='PASS_SEGMENTED_QUEUE_4K_IDENTITY_LIFECYCLE',samples=results,identity_rejections=15,prepare_abort_present_recovery=True,renderer_thread_joined=True,scope='Five actual captured queued4K images and pending identity/recovery; no live timing verification.')
Path('work/camera/prototype-runs/segmented-queue-parity-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
