from pathlib import Path
from PIL import Image,ImageChops
import json
p=Path('work/camera');results=[]
for phase in (0,2,3):
 a=Image.open(p/f'candidate-control-{phase}.ppm');b=Image.open(p/f'candidate-added-{phase}.ppm');d=ImageChops.difference(a,b);c=d.split();mask=ImageChops.lighter(ImageChops.lighter(c[0],c[1]),c[2]);results.append(dict(alpha=phase/4,changed_pixels=sum(x!=0 for x in mask.tobytes()),bbox=d.getbbox()))
assert results[0]['changed_pixels']==results[1]['changed_pixels']==0
assert results[2]['changed_pixels']>0
(p/'single-candidate-tests.json').write_text(json.dumps(dict(result='PASS',samples=results,scope='Single earlier-owned publication-time world candidate diagnostic; identity supplied, not automatic live visibility policy.'),indent=2));print(results)

