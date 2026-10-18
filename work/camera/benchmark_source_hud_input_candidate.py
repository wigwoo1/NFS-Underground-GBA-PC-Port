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
from owned_native_source_palette_table_session_candidate import NativeSourceSession
session=None;results=[]
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
from owned_native_source_sky_pan_session_candidate import NativeSourceSession as Baseline
from owned_native_source_palette_table_session_candidate import NativeSourceSession as Candidate
import statistics
owners=[]
for item in expected:
 alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
 owners.append(OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha)))
reference=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples'];trials=[]
try:
 for trial in range(2):
  pair={}
  for name in (('baseline','table') if trial%2==0 else ('table','baseline')):
   session=(Baseline if name=='baseline' else Candidate)();cost=[]
   try:
    for repeat in range(6):
     for index,owned in enumerate(owners):
      row=session.prepare(owned,1,1,repeat*5+index)
      if repeat==0:
       rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
       import numpy as np
       rgb=np.frombuffer(rgba.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];assert hashlib.sha256(rgb.tobytes()).hexdigest()==reference[index]['rgb_sha256']
      else:cost.append(row['source_prepare_ns'])
      session.abort(1,1,repeat*5+index)
    pair[name]=dict(samples=len(cost),median_source_ms=statistics.median(cost)/1e6,max_source_ms=max(cost)/1e6)
    n=session.source.nf_hud_input_profile_count();assert 0<n<=16384
    profile=(C.c_uint64*(n*7))();session.source.nf_hud_input_profile_read.argtypes=[C.c_void_p,C.c_uint];assert session.source.nf_hud_input_profile_read(profile,n)==1
    entries=[list(profile[i*7:(i+1)*7]) for i in range(n)]
    pair[name]['hud_input']=dict(records=n,copied_bytes=sum(x[6] for x in entries),cache_equal=sum(bool(x[2]) for x in entries),copy_skipped=sum(bool(x[3]) for x in entries),median_wall_ms=statistics.median(x[4] for x in entries)/1e6,max_wall_ms=max(x[4] for x in entries)/1e6)
   finally:session.close()
  trials.append(pair)
finally:cached.close();history.close()
out=dict(result='SOURCE_HUD_INPUT_ACCOUNTING',trials=trials,median_trial_source_ms={k:statistics.median(t[k]['median_source_ms'] for t in trials) for k in ('baseline','table')},scope='Two alternating fullrenderer pairs, same five captured owned samples, one warmup/readback cycle and five measured cycles, exact4Khashes eachpair. Native source callback timing only, no live scene change, Present cadence or whole-game proof.')
Path('work/camera/prototype-runs/source-hud-input-accounting-20261009.json').write_text(json.dumps(out,indent=2));print(out['median_trial_source_ms'])
