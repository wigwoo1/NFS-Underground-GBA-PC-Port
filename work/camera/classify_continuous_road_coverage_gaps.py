from pathlib import Path
import json,struct,collections
p=Path('work/camera');r=json.loads((p/'stable-road-continuous-coverage-gaps-0.json').read_text());b=(p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin').read_bytes();h=struct.unpack_from('<8I',b);checks=[]
for c in r['checks']:
 spans=[]
 for entry in range(h[3]):
  _,ordinal,off,size=struct.unpack_from('<4I',b,32+entry*16)
  if ordinal!=c['command']:continue
  asset=b[off:off+size];ah=struct.unpack_from('<10I',asset)
  spans=[struct.unpack_from('<20I',asset,40+i*80) for i in range(ah[5])]
 assert spans;rows=collections.Counter();reasons=collections.Counter();dup=spill=0
 for pixel in c['missing_pixels']:
  dest=pixel['y']*240+pixel['x'];matches=[]
  for i,s in enumerate(spans):
   base=s[0]-0x0600a000
   for d in range(s[3]+1):
    if base+d*240<=dest<base+d*240+s[1]*2:matches.append(dict(span=i,duplicate_row=bool(d),row_spill=(dest//240!=(base+d*240)//240)))
  assert matches;pixel['original_coverage']=matches;rows[pixel['y']]+=1;reasons[pixel['reason']]+=1;dup+=any(m['duplicate_row'] for m in matches);spill+=any(m['row_spill'] for m in matches)
 assert len(c['missing_pixels'])==c['outside']
 checks.append(dict(command=c['command'],uncovered=c['outside'],reasons=dict(reasons),rows=dict(rows),original_duplicate_row_pixels=dup,original_spill_pixels=spill,details=c['missing_pixels']))
report=dict(result='CLASSIFIED',checks=checks,scope='Every missing full-original pixel classified by native source evaluator failure stage and exact original coverage span. Original span metadata comparison only, never renderer geometry.');(p/'stable-road-coverage-gap-classification.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in c.items() if k!='details'} for c in checks],indent=2))
