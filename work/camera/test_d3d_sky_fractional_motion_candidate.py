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
from owned_native_source_auxiliary_batch_session_candidate import NativeSourceSession
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 session=NativeSourceSession()
 from owned_sky_sampler import SkySamples
 fixed=asset.sample_continuous(*boundaries,.5)
 previous=None
 for index in range(60):
  item=expected[0]
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(SkySamples(fixed.lower,fixed.upper,index/60,fixed.destination))
  row=session.draw(owned,1,1,index)
  rgb=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgb,len(rgb))==0
  import numpy as np
  image=np.frombuffer(rgb.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];row['native_rgb_sha256']=hashlib.sha256(image.tobytes()).hexdigest(); row['sky_weight']=index/60; row['changed_pixels']=None if previous is None else int(np.count_nonzero(np.any(image!=previous,axis=2))); assert previous is None or row['changed_pixels']>0, 'D3D sky pixels held'; previous=image.copy(); results.append(row)

finally:
 if session is not None:session.close();assert session.source.nf_owned_gpu_contexts()==0
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
out=dict(result='PASS_D3D_SKY_FRACTIONAL_PIXEL_MOTION',samples=len(results),changes=[dict(weight=x['sky_weight'],changed_pixels=x['changed_pixels'],sha256=x['native_rgb_sha256']) for x in results],scope='Actual 4K D3D full-scene readback with world and camera frozen and only sky blend varying over 60 weights. Does not prove original-camera phase evolution, live cadence or physical scanout.')
Path('work/camera/prototype-runs/d3d-sky-fractional-motion-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
