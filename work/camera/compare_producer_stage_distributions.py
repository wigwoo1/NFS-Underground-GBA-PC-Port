"""Compare producer stage distributions without attributing causal performance."""
import json,sys,statistics
from pathlib import Path
results={}
for name,path in zip(('baseline','candidate'),sys.argv[1:3]):
 r=json.loads(Path(path).read_text());rows=r['producer_cycle_samples'];stages={}
 for key in rows[0]['stages']:
  v=[x['stages'][key]/1e6 for x in rows];stages[key]=dict(count=len(v),median_ms=statistics.median(v),max_ms=max(v))
 results[name]=stages
out=dict(stages=results,scope='All recorded producer scene extractions; different sequential system loads, no causal or physical presentation proof.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v['sky_attachment_ns'] for k,v in results.items()})
