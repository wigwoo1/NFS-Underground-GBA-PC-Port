from pathlib import Path
from PIL import Image,ImageChops
import json
p=Path('work/camera');a=Image.open(p/'depth-before-140-2.ppm');b=Image.open(p/'entrant-hidden-2.ppm');d=ImageChops.difference(a,b);c=d.split();mask=ImageChops.lighter(ImageChops.lighter(c[0],c[1]),c[2]);report=dict(changed_pixels=sum(x!=0 for x in mask.tobytes()),bbox=d.getbbox(),scope='Exact pose/material controlled comparison with only the new wall made transparent. Diagnostic isolation, not corrected visibility.')
(p/'entrant-isolation-comparison.json').write_text(json.dumps(report,indent=2));print(report)
