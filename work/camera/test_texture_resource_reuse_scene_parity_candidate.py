"""Actual saved fullscene pixels with unchanged and resource-reuse transaction backends."""
import sys,json,ctypes as C,hashlib
from pathlib import Path
import numpy as np
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'actual_saved_scene_setup','exec'))
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
original_cdll=C.CDLL
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
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
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 try:
  session=NativeSourceSession();assert len(loads)==1
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   session.draw(owned,1,1,index)
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  return dict(hashes=hashes,resource_reuses=reused,library=loads[0])
 finally:
  if session is not None:session.close();assert session.source.nf_owned_gpu_contexts()==0
  C.CDLL=original_cdll
try:
 baseline=run('owned-d3d-sky-three-stage-transaction-candidate.dll')
 candidate=run('owned-d3d-texture-resource-reuse-transaction-candidate.dll')
 assert baseline['hashes']==candidate['hashes']
 out=dict(result='PASS_ACTUAL_SCENE_4K_RESOURCE_REUSE_PARITY',frames=len(candidate['hashes']),baseline=baseline,candidate=candidate,scope='Complete 4K RGBA saved fullscene pixels, five original/fractional phases repeated, actual source/HUD/sky/world draw order; limited to one saved scene pair, no sustained gameplay or cadence proof.')
 Path('work/camera/prototype-runs/texture-resource-reuse-scene-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'],'resource_reuses',candidate['resource_reuses'])
finally:cached.close();prepared.close();history.close()
