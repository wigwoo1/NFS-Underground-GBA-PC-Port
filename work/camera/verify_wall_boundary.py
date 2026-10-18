import csv,json
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('work/camera')
def inspect(path):
 rows=list(csv.DictReader(path.open()))
 by={k:[r for r in rows if int(r['case'])==k] for k in range(6)}
 a={int(r['pixel_x']):int(r['red']) for r in by[2] if int(r['green'])==32}
 b={int(r['pixel_x']):int(r['red']) for r in by[3] if int(r['green'])==32}
 delta=[abs(a[x]-b[x])//16 for x in a.keys()&b.keys()]
 return by,dict(common_pixels=len(delta),changed_pixels=sum(d>0 for d in delta),max_palette_jump=max(delta))
_,before=inspect(root/'wall-pixel-sweep-before.csv')
by,after=inspect(root/'wall-pixel-sweep.csv')
assert after['max_palette_jump']<=1 and all(r['mode']=='2' for rr in by.values() for r in rr)
report=dict(result='PASS',synthetic_equal_depth_wall=True,boundary_right_coordinates=[122.99,123.01],before=before,after=after,
 scope='Actual GPU pixel readback with synthetic palettes; does not establish full-game lighting fidelity.')
(root/'wall-boundary-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
im=Image.new('RGB',(840,360),(22,24,30));draw=ImageDraw.Draw(im)
for k,rr in by.items():
 draw.text((8,k*60+4),f"right={rr[0]['right']} native shading (4x horizontal magnification)",fill='white')
 for r in rr:
  x=220+(int(r['pixel_x'])-1918)*4
  draw.rectangle((x,k*60+22,x+3,k*60+48),fill=tuple(int(r[c]) for c in ('red','green','blue')))
im.save(root/'wall-boundary.png')
