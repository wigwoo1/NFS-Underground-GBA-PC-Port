from PIL import Image,ImageChops,ImageDraw
from pathlib import Path
import json,sys
suffix='-'+sys.argv[1] if len(sys.argv)>1 else '';p=Path('work/camera');a=Image.open(p/f'controlled-before{suffix}-2.ppm');b=Image.open(p/f'controlled-after{suffix}-2.ppm');d=ImageChops.difference(a,b);channels=d.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]);changed=sum(x!=0 for x in mask.tobytes());report=dict(changed_pixels=changed,total_pixels=a.width*a.height,bbox=d.getbbox(),scope='Exact camera/object pose; shared world RGBA held fixed. Geometry, draw order and visibility retained from each source snapshot.')
c=Image.new('RGB',(1440,300));draw=ImageDraw.Draw(c)
for i,(im,label) in enumerate([(a,'Before boundary'),(b,'After boundary'),(d,'Absolute difference')]):c.paste(im.resize((480,270)),(i*480,25));draw.text((i*480+8,5),label,fill='white')
c.save(p/f'controlled-comparison{suffix}.png');(p/f'controlled-comparison{suffix}.json').write_text(json.dumps(report,indent=2));print(report)



