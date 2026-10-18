"""Actual captured camera sky on complete interpolated scene; pixel diagnostic."""
import ctypes as C,json,sys,hashlib
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset,SkySamples
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
report='work/camera/prototype-runs/owned-native-1791365534790891100.json'
sys.argv=['setup',report,'0','unused'];ns={}
exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'setup','exec'),ns)
r=json.loads(Path(report).read_text());boundaries=[]
for scene in ns['scenes']:
 s=next(s for s in r['sky_capture_records'] if (s['epoch'],s['publication'])==scene.identity)
 offset=s['source']-0x08000000
 boundaries.append(SkyBoundary(s['epoch'],s['publication'],s['angle'],240,64,0,s['source'],s['asset_origin'],0x06002940,ns['rom'][offset:offset+15136]))
third=ns['r']['model_scene_captures'][2];closed=ns['ClosedGraph'].decode(Path(third['graph']).read_bytes());record=next(s for s in r['sky_capture_records'] if (s['epoch'],s['publication'])==(closed.epoch,closed.refresh));offset=record['source']-0x08000000
boundary_c=SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],record['asset_origin'],0x06002940,ns['rom'][offset:offset+15136])
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,ns['rom'][origin-0x08000000:origin-0x08000000+15376])
assert boundaries[0].angle!=boundaries[1].angle
P=C.c_void_p;d=C.CDLL(str(Path('work/camera/owned-gpu-playable-sky-region-candidate.dll').resolve()))
d.nf_owned_gpu_source_context_callback.argtypes=[P];d.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
alphas=(.001,.2,.4,.5,.6,.8,.999)
cached=PrecomputedSourceWorldSamples(ns['prepared'],alphas,trace=True)
rgb=C.create_string_buffer(3840*2160*3)
def render(value,sky):
 frame,camera,models,bounds,detail=value;offsets,mask,total,_=cached.source_masks[alpha]
 owned=OwnedSourceDraw(bytes(frame),camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(sky)
 rc=d.nf_owned_gpu_source_context_callback(C.byref(owned.context));assert rc==0,(alpha,rc)
 assert d.nf_owned_gpu_read(rgb,len(rgb))==0

 d.nf_owned_gpu_read_region.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,C.c_size_t]
 region=C.create_string_buffer(3240*16*3);assert d.nf_owned_gpu_read_region(300,648,3240,16,region,len(region))==0
 expected=b''.join(rgb.raw[(y*3840+300)*3:(y*3840+3540)*3] for y in range(648,664))
 assert region.raw==expected,'Actual playable sky region differs from completed full4K target'
 sentinel=C.create_string_buffer(b'unchanged');before=sentinel.raw
 assert d.nf_owned_gpu_read_region(300,648,3240,16,sentinel,len(sentinel))!=0 and sentinel.raw==before
 return rgb.raw
checks=[]
try:
 assert d.nf_owned_gpu_window(0)==0
 for alpha in alphas:
  value=cached.sample(alpha);sky=asset.sample_continuous(*boundaries,alpha)
  actual=render(value,sky)
  quantized=render(value,SkySamples(sky.lower,sky.upper,0,sky.destination))
  changed=sum(actual[i:i+3]!=quantized[i:i+3] for i in range(0,len(actual),3))
  assert sky.weight>0 and changed>0,'Complete scene did not expose fractional sky pixels'
  repeated=render(value,sky);assert actual==repeated,'Sky replay nondeterministic'
  checks.append(dict(alpha=alpha,sky_weight=sky.weight,fractional_sky_changed_pixels=changed,full_rgb_sha256=hashlib.sha256(actual).hexdigest(),repeat_exact=True))
 alpha=.5;value=cached.sample(alpha);seam=[];previous=None
 for label,pair,t in [('approach',boundaries,.98),('left_endpoint',boundaries,1),('right_endpoint',[boundaries[1],boundary_c],0),('depart',[boundaries[1],boundary_c],.02)]:
  sky=asset.sample_continuous(*pair,t);pixels=render(value,sky)
  changed=None if previous is None else sum(pixels[i:i+3]!=previous[i:i+3] for i in range(0,len(pixels),3))
  if label=='right_endpoint':assert pixels==previous,'Actual sky pair boundary discontinuity'
  if label in ('left_endpoint','depart'):assert changed>0,'Actual sky movement held beside boundary'
  seam.append(dict(label=label,refreshes=[b.refresh for b in pair],alpha=t,weight=sky.weight,changed_pixels=changed,sha256=hashlib.sha256(pixels).hexdigest()));previous=pixels
 assert asset.sample_continuous(*boundaries,1)==asset.sample_continuous(boundaries[1],boundary_c,0)
finally:
 cached.close();ns['prepared'].close();ns['history'].close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-sky-region-20261008');cp.mkdir(exist_ok=True)
out=dict(result='PASS',source_report=report,refreshes=[b.refresh for b in boundaries],camera_angles=[b.angle for b in boundaries],checks=checks,boundary_checks=seam,third_refresh=boundary_c.refresh,third_angle=boundary_c.angle,scope='Actual captured complete world/HUD/background coverage and camera angle endpoints, seven interpolated poses. Fractional sky changes actual4K pixels relative to zero weight with identical world. Actual playable source-context callback and source model anchors/masks diagnostic, plus actual three-scene sky boundary isolated with held complete-world pose: identical shared endpoint and moving sides. Full-world visibility/geometry boundary continuity and live presentation/scanout timing unverified.')
(cp/'tests.json').write_text(json.dumps(out,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(out))
