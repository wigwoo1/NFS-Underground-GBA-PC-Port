"""Fixed viewport sample comparison; no screen-polygon matching or fitted alignment."""
import json,sys,struct,hashlib
from pathlib import Path
from PIL import Image
cp=Path(sys.argv[1]);r=json.loads((cp/'owned-native-1791388271044014500.json').read_text());checks=[]
for row in r['wall_diagnostic_frames']:
 frame=Path(row['original']).read_bytes();h=struct.unpack_from('<6I2Q',frame);assert 40+sum(h[2:6])==len(frame) and h[1]==row['refresh']
 original=Path(row['original_video']).read_bytes();reference=cp/'original-replay'/f"original-index-{row['input_count']-1:05d}.rgba";assert original==reference.read_bytes()
 native=Image.open(cp/f"native-source-{row['refresh']}.ppm");assert native.size==(3840,2160);pix=native.load();diff=[]
 for y in range(160):
  for x in range(240):
   a=pix[int(300+(x+.5)*13.5),int((y+.5)*13.5)];b=original[(y*240+x)*4:(y*240+x)*4+3];diff.append(tuple(abs(i-j) for i,j in zip(a,b)))
 checks.append(dict(source_refresh=row['refresh'],post_update_refresh=row['original_video_refresh'],input_index=row['input_count']-1,frame_sections=dict(geometry=h[2],hud=h[3],background=h[4],text=h[5]),samples=len(diff),exact_pixels=sum(max(x)==0 for x in diff),pixels_within_8=sum(max(x)<=8 for x in diff),mean_absolute_channel_difference=sum(sum(x) for x in diff)/(3*len(diff)),maximum_channel_difference=max(max(x) for x in diff)))
out=dict(result='MEASURED_FIXED_VIEWPORT_DIFFERENCES',checks=checks,scope='Integer source replay vs exact associated original framebuffer, fixed x=300+13.5*(x+.5), y=13.5*(y+.5) from renderer viewport. No fitted alignment or polygon matching; rasterization/texture sampling can differ. Temporal source/post-update meaning still needs proof; metrics do not certify full fidelity.')
(cp/'fixed-viewport-comparison.json').write_text(json.dumps(out,indent=2));print(out)
