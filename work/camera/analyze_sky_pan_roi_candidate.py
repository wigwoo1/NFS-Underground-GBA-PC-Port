import json,math,struct
from pathlib import Path
import numpy as np
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791512861121558200.json').read_text());links=r['async_sky_links'];pixels=r['async_sky_records'];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();origin=r['sky_capture_records'][0]['asset_origin'];asset=np.frombuffer(rom[origin-0x08000000:origin-0x08000000+15376],np.uint8)
u=(np.arange(512)+.5)*2/27;v=(594+np.arange(64)+.5)*2/27;x=np.floor(u).astype(int);y=np.floor(v).astype(int);i=(y[:,None]-44)*240+x[None,:];rows=[];prior={}
for link,pixel in zip(links,pixels):
 assert (link['epoch'],link['generation'],link['display_index'])==(pixel['epoch'],pixel['generation'],pixel['display_index'])
 commit=link['commit'];assert commit[:3]==[link['epoch'],link['generation'],link['source_older']] and commit[3:5]==[link['refresh'],link['display_index']] and struct.unpack('<Q',struct.pack('<d',link['alpha']))[0]==commit[5]
 a,b=link['sky_source_angles'];delta=((b-a+8192)&16383)-8192;phase=(((a&16383)+delta*link['alpha'])*240/4096)%240;assert abs(phase-math.floor(phase)-link['sky_fraction'])<1e-9
 base=math.floor(phase);upper=(base+1)%240;shift=np.floor(u+np.float32(link['sky_fraction']))>np.floor(u);indices=np.where(shift[None,:],asset[upper+i],asset[base+i]);group=link['display_index']//100
 before=prior.get(group);rows.append(dict(display_index=link['display_index'],phase=phase,source_index_unique=int(len(np.unique(indices))),source_index_changed_pixels=None if before is None else int(np.count_nonzero(indices!=before)),pixel_hash=pixel['rgba_sha256']));prior[group]=indices
candidates=[]
for top in range(594,1390,54):
 v=(top+np.arange(64)+.5)*2/27;y=np.floor(v).astype(int);i=(y[:,None]-44)*240+x[None,:]
 counts=[]
 for link in links:
  a,b=link['sky_source_angles'];delta=((b-a+8192)&16383)-8192;phase=(((a&16383)+delta*link['alpha'])*240/4096)%240;base=math.floor(phase);upper=(base+1)%240;shift=np.floor(u+np.float32(link['sky_fraction']))>np.floor(u)
  indices=np.where(shift[None,:],asset[upper+i],asset[base+i]);counts.append(int(len(np.unique(indices))))
 candidates.append(dict(region=[300,top,512,64],minimum_unique_indices=min(counts),unique_counts=counts))
best=max(candidates,key=lambda c:c['minimum_unique_indices'])
out=dict(recommended_next_roi=best,roi_candidates=candidates,result='PASS_SKY_SAMPLE_IDENTITY_PHASE_LINKS',samples=rows,scope='Exact native commit identity and bit-exact alpha; source index ROI predicted from recovered phase and actual ROM. Palette changes excluded from source-index prediction; physical display timing not certified.')
(p/'prototype-runs/sky-pan-roi-explanation-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
