"""Compare saved disjoint CPU intervals without inferring scanout identity."""
import json,sys,collections
from pathlib import Path
from analyze_consumer_gap_partition import analyze
out=[]
for name,path in [('preview','work/camera/prototype-runs/owned-native-1791439455791998100.json'),('4k','work/camera/prototype-runs/owned-native-1791439868214986400.json')]:
 r=analyze(json.loads(Path(path).read_text()));counts=collections.Counter();totals=collections.Counter()
 for gap in r['largest']:
  parts={x['stage']:x['ms'] for x in gap['parts']};counts[max(parts,key=parts.get)]+=1;totals.update(parts)
 out.append(dict(name=name,gaps=r['gaps'],dominant_stage_counts=dict(counts),summed_disjoint_ms=dict(totals),max_gap_ms=max((x['gap_ms'] for x in r['largest']),default=None)))
result=dict(runs=out,scope='Same originalclock/delay and sourcecontext family, different window build and uncontrolled workload. CPU intervals include scheduling; not exclusive cause or exact ETW/frame attribution.')
Path(sys.argv[1]).write_text(json.dumps(result,indent=2));print(result)
