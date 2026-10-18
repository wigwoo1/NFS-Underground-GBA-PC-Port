import json,ctypes as C,hashlib,numpy as np
from owned_motion_pairs import records
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
batch.SourceFaceDeterminants=SourceFaceDeterminants
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_native_source_backdrop_batch_session_candidate import NativeSourceSession
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};cached=None;session=None;results=[]
try:
 exec(compile(source,'capture_setup','exec'),ns);cached=PrecomputedSourceWorldSamples(ns['prepared'],(.001,.04,.08,.12,.16,.2,.24,.28))
 report=json.loads(Path('work/camera/prototype-runs/owned-native-1791505088586816100.json').read_text());boundaries=[];rom=ns['rom']
 for scene in ns['scenes']:
  r=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);offset=r['source']-0x08000000
  boundaries.append(SkyBoundary(r['epoch'],r['publication'],r['angle'],240,64,0,r['source'],r['asset_origin'],0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);session=NativeSourceSession()
 for i,a in enumerate(cached.samples):
  frame,camera,models,bounds,detail=cached.sample(a);offsets,mask,total,_=cached.source_masks[a]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,a,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,a))
  session.draw(owned,2,1,i*2);rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  baseline=rgba.raw
  target_key=tuple(json.loads(Path('work/camera/prototype-runs/native-rejected-depth-20261008.json').read_text())['models'][0]['key'])
  address_keys=[list(row['key']) for row in records(frame)['records'] if row['kind']==3 and row['key'][1]==50363848]
  target=[j for j,row in enumerate(records(frame)['records']) if row['key']==target_key]
  copied=type(mask).from_buffer_copy(bytes(mask));selected=0
  for j in target:
   selected+=sum(mask[k] for k in range(offsets[j],offsets[j+1]))
   for k in range(offsets[j],offsets[j+1]):copied[k]=0
  suppressed=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,a,offsets,copied,total).attach_sky(asset.sample_continuous(*boundaries,a))
  session.draw(suppressed,2,1,i*2+1);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  changed=int(np.count_nonzero(np.any(np.frombuffer(baseline,np.uint8).reshape(-1,4)!=np.frombuffer(rgba.raw,np.uint8).reshape(-1,4),axis=1)))
  results.append(dict(alpha=a,target_present=bool(target),shared_address_keys=address_keys,target_selected_faces=selected,zero_target_mask_pixel_identical=changed==0,target_contributing_pixels=changed,rgba_sha256=hashlib.sha256(baseline).hexdigest()))
finally:
 if session:session.close();assert session.source.nf_owned_gpu_contexts()==0
 if cached:cached.close()
 for name in ('prepared','history'):
  if ns.get(name):ns[name].close()
assert len(results)==8 and all(x['target_present'] for x in results)
out=dict(result='MEASURED_EXACT_TARGET_VISIBLE_INTERVAL_PIXELS',samples=results,scope='Eight visible-interval poses, actual4K GPU exact target mask suppression comparisons. Measured contribution by target model; no independent correctness proof for other geometry or live scanout.')
Path('work/camera/prototype-runs/native-depth-visible-pixels-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
