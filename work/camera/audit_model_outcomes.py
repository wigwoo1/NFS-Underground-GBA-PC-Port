import json,struct,collections,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());p=Path(r['model_pose_trace']).with_suffix('.outcomes.bin');raw=p.read_bytes();assert len(raw)%32==0;counts=collections.Counter();rows=[]
for at in range(0,len(raw),32):
 h=struct.unpack_from('<8I',raw,at);assert h[0]==0x314f4d4e
 if 9945<=h[1]<=9965:
  model=(h[3]-0x08331624)//40+1;counts[(model,h[4],h[6])]+=1;rows.append(list(h))
out=dict(records=len(raw)//32,boundary_counts=[dict(model=k[0],row_plan_ok=k[1],write_ok=k[2],count=n) for k,n in sorted(counts.items())],rows=rows);p.with_suffix('.json').write_text(json.dumps(out,indent=2));print(out['boundary_counts'])
