"""Characterize wall raster mask separation without imposing a parity threshold."""
import json,struct,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scene_batches import batches
path=Path(sys.argv[1]);coverage=json.loads(path.read_text());overlaps_path=path.with_name(path.stem.replace('-scene-coverage','')+'.json');overlaps=json.loads(overlaps_path.read_text());capture=json.loads(Path(overlaps['source_report']).read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256']
selected={(tuple(c['interval']),c['draw_id']):c for c in coverage['checks'] if c['kind']==2};results=[]
def expanded(mask,radius):
 pad=np.pad(mask,radius);out=np.zeros_like(mask)
 for y in range(radius*2+1):
  for x in range(radius*2+1):out|=pad[y:y+160,x:x+240]
 return out
for batch in batches(trace):
 pending={};key=(batch['begin_refresh'],batch['end_refresh'])
 for e in batch['events']:
  if e['pc']!=0xffff0084:continue
  stage,identity,*_=struct.unpack('<8I',e['blocks'][85][1][:32]);c=selected.get((key,identity))
  if not c:continue
  start=batch['display_page']*0xa000;raw=np.frombuffer(e['blocks'][84][1],np.uint8)[start:start+38400]
  if stage==0:pending[identity]=raw.copy();continue
  if identity not in pending:continue
  original=(pending.pop(identity)!=raw).reshape(160,240)
  label=f'scene-coverage-{key[0]}-{identity}';root=Path(__file__).resolve().parent/'prototype-runs';ys=((np.arange(160)+.5)*13.5).astype(int);xs=(300+(np.arange(240)+.5)*13.5).astype(int)
  a=np.asarray(Image.open(root/(label+'-before.ppm-0.ppm')))[ys[:,None],xs];b=np.asarray(Image.open(root/(label+'-after.ppm-0.ppm')))[ys[:,None],xs];native=np.any(a!=b,axis=2)
  assert int(original.sum())==c['original_changed_pixels'] and int(native.sum())==c['native_center_changed_pixels']
  distances=[dict(radius=r,original_outside=int((original&~expanded(native,r)).sum()),native_outside=int((native&~expanded(original,r)).sum())) for r in range(5)]
  results.append(dict(interval=key,draw_id=identity,source=c['source'],distances=distances))
assert len(results)==len(selected)==48
summary=[dict(radius=r,original_outside=sum(c['distances'][r]['original_outside'] for c in results),native_outside=sum(c['distances'][r]['native_outside'] for c in results)) for r in range(5)]
out=path.with_name(path.stem+'-wall-distances.json');out.write_text(json.dumps(dict(result='MEASURED',coverage_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=results,summary=summary,scope='Original value-change masks and current native command-prefix images: Chebyshev pixel-neighborhood distances only. No threshold accepts parity; broad discrepancies, quantized original terminal coverage and texture/zero-write differences require further source evidence.'),indent=2));print(json.dumps(summary))
