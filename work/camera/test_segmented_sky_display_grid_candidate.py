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
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);worker=NativeSourceWorker();results=[]

try:
 alpha=expected[0]['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
 for index,item in enumerate(expected):
  phase=item['alpha'];sky=asset.sample_continuous(*boundaries,phase)
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(sky)
  row=worker.prepare(owned,1,1,index,True).result(20);worker.present(1,1,index).result(20)
  results.append(dict(index=index,phase=phase,weight=sky.weight,rgba_rgb_sha256=row['native_rgb_sha256']))
 Path('work/camera/prototype-runs/segmented-sky-display-grid-diagnostic-20261009.json').write_text(json.dumps(dict(source_angles=[x.angle for x in boundaries],unique_images=len(set(x['rgba_rgb_sha256'] for x in results)),samples=results),indent=2))
 assert all(a['rgba_rgb_sha256']!=b['rgba_rgb_sha256'] for a,b in zip(results,results[1:])), 'Sky pixels repeat despite changed phase'
finally:worker.close();cached.close();history.close()
assert not worker.thread.is_alive() and worker.error is None
out=dict(result='PASS_SEGMENTED_4K_SKY_CAPTURED_DISPLAY_GRID',source_angles=[x.angle for x in boundaries],unique_images=len(set(x['rgba_rgb_sha256'] for x in results)),samples=results,scope='Captured interval display-grid diagnostic4Kreadbacks with fixed world/camera/model/visibility data and varying captured sky phase only. Confirms fractional sky pixels at captured grid phases, not realtime60fps, scanout or allscene gameplay.')
Path('work/camera/prototype-runs/segmented-sky-display-grid-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],out['source_angles'],out['unique_images'])
