"""60 Hz sky phase regression; synthetic owned texture, no game timing mutation."""
import json, math
from pathlib import Path
from owned_sky_sampler import SkyAsset
from owned_sky_boundary import SkyBoundary
from owned_sky_scroll import source_offset

def main():
 asset=SkyAsset(0x08010000,bytes(i%251 for i in range(15376)))
 def boundary(angle,refresh):
  offset=source_offset(angle,240,0)
  return SkyBoundary(1,refresh,angle,240,64,0,asset.origin+offset,asset.origin,0x06002940,asset.data[offset:offset+15136])
 checks=0;moving=0
 # Five original updates span slightly over five 60 Hz presentation intervals.
 interval=5*280896/16777216
 for start,delta in [(100,1),(100,-1),(16383,1),(0,-1),(4095,2),(4096,-2),(16000,120),(300,-120)]:
  a=boundary(start,1);b=boundary((start+delta)&16383,6)
  prior=None
  for tick in range(6):
   alpha=(tick/60)/interval
   sample=asset.sample_continuous(a,b,alpha)
   phase=((start+delta*alpha)*240/4096)%240
   base=math.floor(phase)
   assert sample.lower==asset.data[base:base+15136]
   upper=(base+1)%240
   assert sample.upper==asset.data[upper:upper+15136]
   assert abs(sample.weight-(phase-base))<1e-12
   if prior is not None:
    step=((phase-prior+120)%240)-120
    assert abs(step-delta*240/4096/(60*interval))<1e-10
    assert step!=0
    moving+=1
   prior=phase;checks+=1
  c=boundary((start+2*delta)&16383,11)
  assert asset.sample_continuous(a,b,1)==asset.sample_continuous(b,c,0)
 result=dict(result='PASS',samples=checks,moving_transitions=moving,pair_boundaries=8,original_interval_seconds=interval,scope='Synthetic owned sky sampling at 60 Hz, slow forward/reverse turns and angle/texture seams. No GPU pixels or physical scanout certification.')
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-60hz-phase-regression-20261007');cp.mkdir(exist_ok=True)
 (cp/'result.json').write_text(json.dumps(result,indent=2))
 (cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
 print(json.dumps(result))
if __name__=='__main__':main()
