"""Fixed full scene: fractional sky changes through actual native DXGI batch."""
from pathlib import Path
source=Path('work/camera/test_dx_native_batch_present.py').read_text()
exec(compile(source.split('try:')[0],'batch-setup','exec'))
from owned_sky_sampler import SkySamples
source_report=json.loads(Path(report).read_text());boundaries=[]
for scene in ns['scenes']:
 record=next(x for x in source_report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],record['asset_origin'],0x06002940,ns['rom'][offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,ns['rom'][origin-0x08000000:origin-0x08000000+15376])
sky=asset.sample_continuous(*boundaries,.5);value=ns['prepared'].sample(.5);epoch=boundaries[0].epoch
q=h.nf_owned_handoff_create(epoch);checks=[];previous=None
try:
 assert gpu.nf_owned_gpu_window(1)==0
 for index,weight in enumerate((.2,.4,.6,.8)):
  fractional=SkySamples(sky.lower,sky.upper,weight,sky.destination)
  row=(boundaries[0].refresh,boundaries[1].refresh,index,0,.5,value,fractional)
  owned=OwnedPresentationBatch(epoch,[row])
  assert batch(q,epoch,1,owned.items,1,draw,present,owned.samples,owned.waits,owned.stages,C.byref(owned.completed))==1
  assert owned.completed.value==1 and owned.draws[0].result==owned.presents[0].result==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
  pixels=rgb.raw
  changed=None if previous is None else sum(a!=b for a,b in zip(previous,pixels))
  if previous is not None: assert changed>0,'Full-scene native batch froze fractional sky'
  out=(U*16)();assert probe.nf_dx_bridge_diagnostic(out)==0 and out[9]==1
  checks.append(dict(weight=weight,changed_rgb_channels=changed,dxgi_backbuffer_exact=True));previous=pixels
finally:
 assert probe.nf_dx_bridge_close()==0
 if q:h.nf_owned_handoff_destroy(q)
 assert gpu.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/fullscene-sky-subpixel-batch-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Fixed complete captured scene; only sky fractional weight changes via current native batch/DXGI callback. Actual4K readback and exactDXGIbackbuffer parity; diagnostic not live scanout cadence'),indent=2))
(cp/'test_fullscene_sky_subpixel_batch.py').write_text(Path(__file__).read_text())
print(json.dumps(checks));print('PASS full-scene DXGI fractional sky updates')
