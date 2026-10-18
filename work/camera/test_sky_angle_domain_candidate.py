"""Exhaustive original-angle domain for continuous source sky sampling."""
import csv,json,hashlib,math
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
from owned_sky_scroll import source_offset
rompath=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
rom=rompath.read_bytes()
assert hashlib.sha256(rom).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'
row=next(r for r in csv.DictReader(Path('work/camera/sky-caller-trace.csv').open()) if r['wrapper_saved_return']=='08004cb9' and r['height']=='63' and int(r['sky_center'])==0)
origin=int(row['source'],16)-source_offset(int(row['sky_angle'],16),240,0)
asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
def boundary(angle,refresh):
 offset=source_offset(angle,240,0)
 return SkyBoundary(2,refresh,angle,240,64,0,origin+offset,origin,int(row['destination'],16),asset.data[offset:offset+15136])
checks=0;seams=0
for delta in (1,-1,8,-8):
 for angle in range(16384):
  a=boundary(angle,1); b=boundary((angle+delta)&16383,2); c=boundary((angle+2*delta)&16383,3)
  assert asset.sample(a,b,0).lower==a.indices and asset.sample(a,b,1).lower==b.indices
  for alpha in (0,.125,.5,.875,1):
   result=asset.sample_continuous(a,b,alpha)
   phase=((angle+delta*alpha)*240/4096)%240
   base=math.floor(phase)
   assert result.lower==asset.data[base:base+15136]
   assert result.upper==asset.data[(base+1)%240:(base+1)%240+15136]
   assert abs(result.weight-(phase-base))<1e-12
   assert len(result.lower)==len(result.upper)==15136
   checks+=1
  assert asset.sample_continuous(a,b,1)==asset.sample_continuous(b,c,0)
  if angle in (4095,8191,12287,16383):seams+=1
out={'result':'PASS_EXHAUSTIVE_SOURCE_SKY_ANGLE_DOMAIN','angles':16384,'intermediate_and_endpoint_samples':checks,'turn_deltas':[1,-1,8,-8],'pair_continuity_checks':65536,'original_endpoint_checks':131072,'explicit_seam_start_checks':seams,'asset_origin':origin,'asset_sha256':hashlib.sha256(asset.data).hexdigest(),'scope':'Actual ROM bytes, every 14-bit angle, positive/negative one- and eight-unit turns, fractional phases and partial final row. Does not cover all larger turn intervals, palette conversion, GPU spatial filtering, live cadence or physical scanout.'}
path=Path('outputs/nfsug-native-renderer/camera-research/sky-angle-domain-20261009.json');path.write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))

