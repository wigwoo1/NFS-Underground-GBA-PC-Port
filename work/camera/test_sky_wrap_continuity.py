from pathlib import Path
import json
from owned_sky_sampler import SkyAsset,SkySamples
from owned_sky_color import sky_rgba
s={};exec(Path('work/camera/test_owned_sky_boundary.py').read_text().split("out=Path(")[0],s);r=s['records'];origin=r[0].asset_origin;raw=s['rom'];data=raw[origin-0x08000000:origin-0x08000000+15376];asset=SkyAsset(origin,data)
palette=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-state-parity-20261006/sky-caller-probe.dll-palette.bin').read_bytes()[:512]*160
wraps=[(a,b) for a,b in zip(r,r[1:]) if abs(a.source-b.source)>120];assert len(wraps)==15
for a,b in wraps:
 lo=a.source-origin;hi=b.source-origin
 travel=(hi-lo+120)%240-120;seam=(240-lo)/travel if travel>0 else -lo/travel
 assert 0<=seam<=1
 target=sky_rgba(SkySamples(data[:15136],data[:15136],0,a.destination),palette)
 for alpha in (max(0,seam-1e-9),min(1,seam+1e-9)):
  sample=asset.sample(a,b,alpha)
  assert sky_rgba(sample,palette)==target
 assert asset.sample(a,b,0).lower==a.indices and asset.sample(a,b,1).lower==b.indices
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-wrap-continuity-20261006')
for name in ('owned_sky_sampler.py','test_sky_wrap_continuity.py'):(cp/name).write_text((Path('work/camera')/name).read_text())
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',wrap_intervals=len(wraps),original_rom_seam_differing_indices=sum(x!=y for x,y in zip(data[:15136],data[240:15376])),scope='Forward/reverse fractional phase seam converges to exact phase0 palette colors, original endpoints retained. Not live steering/scanout proof'),indent=2));print('PASS15 forward/reverse sky wraps')
