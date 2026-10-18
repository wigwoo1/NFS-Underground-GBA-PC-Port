from pathlib import Path
import json
from owned_sky_sampler import SkyAsset
s={};exec(Path('work/camera/test_owned_sky_boundary.py').read_text().split('out=Path(')[0],s)
r=s['records'];origin=r[0].asset_origin;rom=s['rom'];asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
small=0
for a,b in zip(r,r[1:]):
 delta=((b.angle-a.angle+8192)&16383)-8192
 samples=[asset.sample_continuous(a,b,x/16) for x in range(17)]
 assert all(len(x.lower)==len(x.upper)==15136 and 0<=x.weight<1 for x in samples)
 if delta and a.source==b.source:
  assert samples[0]!=samples[-1];small+=1
for a,b,c in zip(r,r[1:],r[2:]):
 end=asset.sample_continuous(a,b,1);start=asset.sample_continuous(b,c,0)
 assert (end.lower,end.upper,end.weight)==(start.lower,start.upper,start.weight)
assert small==30
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-continuous-phase-20261006')
(out/'component.json').write_text(json.dumps(dict(result='PASS',intervals=160,samples=2720,small_turns=small,pair_boundary_checks=159,scope='Continuous native sky phase component; live integration pending'),indent=2))
print('PASS continuous sky phase:30 small turns,159 pair boundaries,2720 samples')
