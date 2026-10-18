import owned_segmented_display_placement_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_source_draw_type_reuse_install_candidate
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
namespace={};exec(compile(Path('work/camera/owned_source_segmented_draw_candidate.py').read_text(),'original_draw_source','exec'),namespace);OriginalDraw=namespace['OwnedSourceDraw']

folder=Path('work/camera/prototype-runs/draw-construction-fixture-20261009');folder.mkdir(exist_ok=True)
(folder/'base.bin').write_bytes(frames[0]);items=[]
for item in expected:
 alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
 items.append(dict(camera=list(camera),models=list(models),bounds=list(bounds),count=detail['geometry_records'],sources=[list(x) for x in cached.source_cameras],alpha=alpha,offsets=list(offsets),mask=list(mask),total=total))
(folder/'inputs.json').write_text(json.dumps(items));worker.close();cached.close();history.close();print(folder)
