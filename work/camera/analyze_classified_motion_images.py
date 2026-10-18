from pathlib import Path
import json,csv,hashlib,sys
from PIL import Image,ImageDraw
import numpy as np
p=Path('work/camera');prefix=sys.argv[1] if len(sys.argv)>1 else 'classified-motion';files=sorted(p.glob(prefix+'-*.ppm'));assert len(files)==12
rows=[r for r in csv.DictReader((p/'live-paired-parity.csv').open()) if int(r['ready'])][180:192];assert len(rows)==12
frames=[np.asarray(Image.open(f)) for f in files];assert all(a.shape==(2160,3840,3) for a in frames)
changes=[]
for i,(a,b) in enumerate(zip(frames,frames[1:])):
 mask=np.any(a!=b,axis=2);assert mask.any();changes.append(dict(pair=i,changed_pixels=int(mask.sum()),road_lower_changed=int(mask[1080:2050,300:3540].sum()),world_upper_changed=int(mask[300:1080,300:3540].sum()),display_gap=int(rows[i+1]['display_index'])-int(rows[i]['display_index']),target_gap=float(rows[i+1]['target'])-float(rows[i]['target'])))
canvas=Image.new('RGB',(1280,750),(30,30,30));draw=ImageDraw.Draw(canvas)
for i,f in enumerate(files):
 im=Image.open(f);im.thumbnail((320,180));x=i%4*320;y=i//4*250;canvas.paste(im,(x,y));draw.text((x+5,y+183),f'{i}: display {rows[i]["display_index"]}',fill='white')
canvas.save(p/(prefix+'-contact.png'))
if '--consecutive' in sys.argv:assert all(c['display_gap']==1 for c in changes)
report=dict(result='PASS',frames=12,dimensions=[3840,2160],unique_frames=len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames}),transitions=changes,scope='12 captured complete native images change across sampled scene regions; GPU readback/disk writes disturb cadence, so not smooth60fps or original visual parity evidence.')
if '--consecutive' in sys.argv:report['scope']='12 consecutive complete native4K frames sampled at60Hz display targets; deferred disk writes, GPU readback still present; no physical scanout or original whole-scene fidelity proof.'
(p/(prefix+'-image-tests.json')).write_text(json.dumps(report,indent=2));print(report)
