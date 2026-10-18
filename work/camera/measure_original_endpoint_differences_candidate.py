import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
root=Path('outputs/nfsug-native-renderer/camera-research/aligned-moving-images-20261009')
rows=[]
# Fixed game-pixel centers in the renderer's documented 3240x2160 viewport.
# This measures rendered output only; it does not fit or recover geometry.
x=np.floor(300+(np.arange(240)+.5)*13.5).astype(int)
y=np.floor((np.arange(160)+.5)*13.5).astype(int)
regions={'whole_frame':(0,0,240,160),'timer':(0,0,80,24),'left_gauge':(0,38,22,112),'right_speedometer':(180,98,240,160),'car_and_road':(70,96,178,150),'background_buildings':(84,20,236,90)}
for i,refresh in enumerate((9103,9106)):
 p=root/f'native-exact-endpoint-{i}.png';q=root/f'original-{refresh}.png'
 native=np.array(Image.open(p).convert('RGB'));original=np.array(Image.open(q).convert('RGB'))
 assert native.shape==(2160,3840,3) and original.shape==(160,240,3)
 sampled=native[y[:,None],x[None,:]]
 difference=np.abs(sampled.astype(np.int16)-original.astype(np.int16))
 result={}
 for name,(a,b,c,d) in regions.items():
  v=difference[b:d,a:c];result[name]={'pixels':int(v.shape[0]*v.shape[1]),'mean_absolute_channel_error':float(v.mean()),'max_channel_error':int(v.max()),'exact_rgb_fraction':float(np.all(v==0,axis=2).mean()),'within_8_all_channels_fraction':float(np.all(v<=8,axis=2).mean())}
 # Fixed HUD regions: isolate bright cyan/white original glyph pixels from
 # underlying textured world, without moving or aligning any pixels.
 hud={}
 for name in ('timer','left_gauge','right_speedometer'):
  a,b,c,d=regions[name];o=original[b:d,a:c].astype(np.int16);n=sampled[b:d,a:c].astype(np.int16)
  mask=((o[:,:,1]>180)&(o[:,:,2]>180)&(o[:,:,0]<100))|np.all(o>245,axis=2)
  delta=np.abs(o-n)[mask]
  hud[name]={'selected_original_glyph_pixels':int(mask.sum()),'exact_rgb_fraction':float(np.all(delta==0,axis=1).mean()) if len(delta) else None,'mean_absolute_channel_error':float(delta.mean()) if len(delta) else None}
 rows.append({'hud_glyph_diagnostics':hud,'epoch':2,'refresh':refresh,'native_png_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_png_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'regions':result})
out={'result':'MEASURED_ORIGINAL_ENDPOINT_DIFFERENCES','sampling':'Fixed original pixel centers using documented viewport x300,width3240,height2160,scale13.5. No image alignment or polygon matching.','scope':'Two exact endpoints only. Original GBA rasterization and native rasterization differ; these are diagnostic measurements, not a fidelity pass threshold. Regions are fixed rectangles and may contain multiple layers.','frames':rows}
Path('work/camera/prototype-runs/original-endpoint-differences-20261009.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
