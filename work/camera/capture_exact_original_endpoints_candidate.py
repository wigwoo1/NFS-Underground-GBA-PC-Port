import owned_scenery_thread_library_install_candidate
import owned_endpoint_road_planner as road_planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_viewport_bounds_fixed_types_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import owned_ordered_render_tail_install_candidate
import owned_source_packet_phase_profile_install_candidate
"""Actual saved fullscene pixels with unchanged and resource-reuse transaction backends."""
import sys,json,ctypes as C,hashlib
from pathlib import Path
import numpy as np
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791604009325159000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
setup=setup.replace("meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])","folder=Path('work/camera/prototype-runs/child-scene-1791604003744272300')")
setup=setup.replace("expected=json.loads((folder/'prepared-signatures.json').read_text())","expected=[]")
exec(compile(setup,'actual_saved_scene_setup','exec'))
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
expected=[dict(alpha=a) for a in (0,1)]
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch_module
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=None
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
def run(library):
 loads=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  if Path(path).name.startswith('owned-gpu-source-'):
   path=str(Path(path).with_name('owned-original-endpoint-candidate.dll'))
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 try:
  session=NativeSourceSession()
  session.source.nf_original_endpoint_callback.argtypes=[C.c_void_p]
  session.source.nf_owned_gpu_source_context_callback=session.source.nf_original_endpoint_callback
  assert len(loads)==1
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame=frames[int(alpha)]
   sky=asset.sample_continuous(*boundaries,alpha)
   from types import SimpleNamespace
   from live_native_transaction_candidate import DrawContext
   owners=[C.create_string_buffer(frame),C.create_string_buffer(sky.lower),C.create_string_buffer(sky.upper)]
   context=DrawContext(C.addressof(owners[0]),len(frame),None,None,None,0,C.addressof(owners[1]),C.addressof(owners[2]),15136,sky.weight,-999,0,0,0)
   owned=SimpleNamespace(frame=frame,context=context,owners=owners,segmented=False)
   before=bytes(owners[0].raw[:len(frame)])
   assert session.source.nf_original_endpoint_callback(None)==37
   for field,value in [('camera',1),('models',1),('bounds',1),('skycount',15135),('weight',1.0)]:
    saved=getattr(context,field);setattr(context,field,value)
    assert session.source.nf_original_endpoint_callback(C.byref(context))==37
    assert context.result==-999 and bytes(owners[0].raw[:len(frame)])==before
    setattr(context,field,saved)
   session.draw(owned,1,1,index)
   assert bytes(owners[0].raw[:len(frame)])==before==frame
   assert not context.camera and not context.models and not context.bounds and context.skycount==15136
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
   if library=='owned-d3d-world-stream-linear-transaction-candidate.dll' and index in (0,1):
    from PIL import Image
    output=Path('outputs/nfsug-native-renderer/camera-research/aligned-moving-images-20261009');output.mkdir(exist_ok=True)
    Image.frombytes('RGBA',(3840,2160),rgba.raw).save(output/('native-exact-endpoint-'+str(index)+'.png'))
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>=0 # Later pair may have no reusable material uploads; pixel equality remains required.
  return dict(hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   owners=(C.c_uint64*3)();assert session.source.nf_hud_owner_stats(owners)==1 and list(owners)==[0,0,0]
  C.CDLL=original_cdll
try:
 baseline=run('owned-d3d-sky-linear-transaction-candidate.dll')
 candidate=run('owned-d3d-world-stream-linear-transaction-candidate.dll')
 assert baseline['hashes']==candidate['hashes']
 out=dict(result='PASS_EXACT_ORIGINAL_ENDPOINT_FULL4K_PARITY',frames=len(candidate['hashes']),alphas=[x['alpha'] for x in expected],baseline=baseline,candidate=candidate,scope='Two exact retained original endpoint frames at epoch2 refresh9103/9106, repeated full4K RGBA equality across filtered baseline/current world-stream backend. No interpolation pose/mask overrides. Diagnostic only; no original-game pixel fidelity or cadence claim.')
 Path('work/camera/prototype-runs/aligned-exact-endpoint-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'],'resource_reuses',candidate['resource_reuses'])
finally:prepared.close();history.close()
