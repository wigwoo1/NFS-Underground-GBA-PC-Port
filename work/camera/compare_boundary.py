from PIL import Image,ImageChops,ImageDraw
from pathlib import Path
import json
p=Path('work/camera');a=Image.open(p/'boundary-before-2.ppm');b=Image.open(p/'boundary-after-2.ppm');d=ImageChops.difference(a,b);channels=d.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]);changed=sum(x!=0 for x in mask.tobytes());report=dict(changed_pixels=changed,total_pixels=a.width*a.height,bbox=d.getbbox(),scope='Near-identical pose across complete snapshot change; differences include visibility, order and materials, not isolated order changes.')
c=Image.new('RGB',(1440,300));draw=ImageDraw.Draw(c)
for i,(im,label) in enumerate([(a,'Before boundary'),(b,'After boundary'),(d,'Absolute difference')]):c.paste(im.resize((480,270)),(i*480,25));draw.text((i*480+8,5),label,fill='white')
c.save(p/'boundary-comparison.png');(p/'boundary-comparison.json').write_text(json.dumps(report,indent=2));print(report)

