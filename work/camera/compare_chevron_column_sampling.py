"""Compare original columns with continuous sampling of recovered world geometry."""
from pathlib import Path
import json,math,collections
p=Path('outputs/nfsug-native-renderer/camera-research')
capture=json.loads((p/'original-wall-column-audit.json').read_text())
audit=json.loads((p/'native-wall-invocation-audit.json').read_text())
world=json.loads((p/'native-world-audit.json').read_text())
surface=next(s for s in world['surfaces'] if s['source']=='0x857c6f4')
view=[v if v<2**31 else v-2**32 for v in audit['visibility_poses'][0]['view']]
points=[]
for (x,y,z),uv in zip(surface['vertices'],surface['uv']):
 x+=view[9];y+=view[10];z+=view[11]
 cx=(x*view[0]+z*view[6])/16384;cz=(x*view[2]+z*view[8])/16384
 points.append([120+128*cx/cz,87+128*y/cz,cz,*uv])
def sample(x,y):
 for ids in ((0,1,2),(0,2,3)):
  a,b,c=[points[i] for i in ids]
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
  wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
  if min(wa,wb,wc)<0:continue
  q=wa/a[2]+wb/b[2]+wc/c[2]
  return [sum(w*t[k]/t[2] for w,t in zip((wa,wb,wc),(a,b,c)))/q for k in (3,4)]
 return None
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
columns=[c for c in capture['selected_columns'] if c['texture']=='0x83e6ddc'];assert len(columns)==14
counts=collections.Counter();records=[];width,height=surface['texture_size'];base=int(columns[0]['texture'],16)
for column in columns:
 state=column['state'];destination=int(column['destination'],16)+state[2]*(state[1]>>14)*2
 for original_address in column['source_addresses']:
  page=0x0600a000 if destination>=0x0600a000 else 0x06000000;logical=destination-page;x=logical%240;y=logical//240
  original_index=rom[original_address-0x08000000]
  # Actual GBA VRAM byte stores replicate across the aligned halfword.
  for pair_pixel in (0,1):
   uv=sample(x+pair_pixel+.5,y+.5);counts['original_pair_pixels']+=1
   if uv is None:counts['outside_continuous_geometry']+=1;continue
   tx=math.floor(uv[0]*width)%width;ty=math.floor(uv[1]*height)%height
   continuous_address=base+ty*width+tx;continuous_index=rom[continuous_address-0x08000000]
   counts['inside_continuous_geometry']+=1
   counts['same_texel_address' if continuous_address==original_address else 'different_texel_address']+=1
   counts['same_index' if continuous_index==original_index else 'different_index']+=1
   counts['same_zero_coverage' if bool(continuous_index)==bool(original_index) else 'different_zero_coverage']+=1
   records.append(dict(x=x+pair_pixel,y=y,original_texel=[(original_address-base)%width,(original_address-base)//width],continuous_texel=[tx,ty],original_index=original_index,continuous_index=continuous_index))
  destination+=state[2]*2
report=dict(result='COMPARED',columns=14,counts=dict(counts),world_projected_points=points,samples=records,scope='Original complete paired column reads versus continuous perspective at same older camera, using recovered world geometry. Quantifies raster/texel differences; does not assert these alone explain full-scene discrepancy or justify upscaling.')
(p/'chevron-column-continuous-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(columns=14,counts=dict(counts)),indent=2))
