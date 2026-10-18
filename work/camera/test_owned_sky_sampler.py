import runpy,json,math
from pathlib import Path
from owned_sky_sampler import SkyAsset
s=runpy.run_path('work/camera/test_owned_sky_boundary.py');records=s['records'];rom=s['rom'];origin=records[0].asset_origin
mutable=bytearray(rom[origin-0x08000000:origin-0x08000000+15376]);asset=SkyAsset(origin,mutable);mutable[0]^=255
samples=0;wraps=0;fractional=0
for a,b in zip(records,records[1:]):
 assert asset.sample(a,b,0).lower==a.indices and asset.sample(a,b,1).lower==b.indices
 if abs(b.source-a.source)>120:wraps+=1
 for alpha in (.125,.25,.5,.75,.875):
  x=asset.sample(a,b,alpha);assert len(x.lower)==len(x.upper)==15136 and 0<=x.weight<1
  samples+=1;fractional+=0<x.weight<1
negative=0
for alpha in (-1,2,float('nan'),float('inf')):
 try:asset.sample(records[0],records[1],alpha)
 except ValueError:negative+=1
 else:raise AssertionError('Invalid fraction accepted')
from dataclasses import replace
bad=replace(records[0],indices=bytes([records[0].indices[0]^255])+records[0].indices[1:])
try:asset.verify(bad)
except ValueError:negative+=1
else:raise AssertionError('Mismatched endpoint accepted')
assert fractional and wraps==15
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-fractional-sampler-20261006');out.mkdir(exist_ok=True)
for name in ('owned_sky_sampler.py','test_owned_sky_sampler.py'):(out/name).write_text((Path('work/camera')/name).read_text())
(out/'tests.json').write_text(json.dumps(dict(result='PASS',endpoint_checks=320,intermediate_samples=samples,fractional_samples=fractional,wrap_intervals=wraps,negative_checks=negative,scope='Original ROM indexed endpoint bytes and bounded fractional source sampling; no palette/GPU/live60fps proof'),indent=2));print('PASS fractional sky',samples,fractional,wraps)
