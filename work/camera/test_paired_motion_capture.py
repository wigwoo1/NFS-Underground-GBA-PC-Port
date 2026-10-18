from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
p=Path('work/camera');files=sorted(p.glob('paired-motion-*.ppm'));assert len(files)==12
sheet=Image.new('RGB',(1920,870));draw=ImageDraw.Draw(sheet);previous=None;rows=[]
for i,f in enumerate(files):
 with Image.open(f) as im:
  assert im.size==(3840,2160);rgb=im.convert('RGB');small=rgb.resize((480,270));a=np.asarray(small).astype(np.int16);row=dict(frame=i,sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),nonblack_fraction=float(np.any(a>0,axis=2).mean()))
  if previous is not None:row['mean_absolute_rgb_change']=float(np.abs(a-previous).mean());row['changed_pixel_fraction']=float(np.any(a!=previous,axis=2).mean())
  previous=a;rows.append(row);x=(i%4)*480;y=(i//4)*290;sheet.paste(small,(x,y));draw.text((x+8,y+272),str(i),fill='white')
sheet.save(p/'paired-motion-contact.png');report=dict(result='CAPTURED',frames=12,dimensions=[3840,2160],scope='Consecutive live paired GPU frame readbacks; readback and disk writes perturb timing; visual inspection pending, not60fpsverification',images=rows);(p/'paired-motion-capture-tests.json').write_text(json.dumps(report,indent=2));print(rows[1:3])
