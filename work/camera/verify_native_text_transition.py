"""Original final RGB parity for retained glyph cells across selection page flip."""
from pathlib import Path
from PIL import Image
import json,sys
p=Path('work/camera/prototype-runs')
original=p/'text-transition-original-1fdf6660f8764efcad1ed4b1cd024e6a'
prefix=p/(sys.argv[1] if len(sys.argv)>1 else 'threaded-prepared-6decc3debc6c4d5c82c38d335078a5a9')
rows=[]
for meta in sorted(p.glob(prefix.name+'-dense-*-native-source.json')):
 base=str(meta).removesuffix('-native-source.json');m=json.loads(meta.read_text());refresh=int(m['target']);text=Path(base+'-owned-text.bin').read_bytes();rgb=Path(str(original)+'-original-pixels-'+str(refresh)+'.bin').read_bytes();im=Image.open(base+'-native.ppm');hits=0;bad=[]
 for y in range(160):
  for x,c in enumerate(text[y*480+240:(y+1)*480]):
   if c:
    hits+=1;a=im.getpixel((int(300+(x+.5)*13.5),int((y+.5)*13.5)));b=tuple(rgb[(y*240+x)*4:(y*240+x)*4+3])
    if a!=b:bad.append([x,y,list(a),list(b)])
 rows.append(dict(refresh=refresh,covered=hits,mismatches=len(bad),samples=bad[:8],source=m['source_refreshes']))
assert len(rows)==30
for row in rows:
 if 3544<=row['refresh']<=3548:assert row['covered']==328, row
report=dict(result='PASS' if all(not r['mismatches'] for r in rows) else 'FAIL',frames=len(rows),covered_cell_comparisons=sum(r['covered'] for r in rows),mismatches=sum(r['mismatches'] for r in rows),rows=rows,scope='Only retained text coverage, sampled centers of each original cell at4K; missing glyph coverage is not measured.')
Path(str(prefix)+'-text-transition-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
