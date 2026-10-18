import json,sys,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());stages=collections.defaultdict(list)
for row in r['presentation_samples']:
 for entry in (row.get('prepared') or {}).get('consumer_stages',[]):
  if entry['stage'].endswith('_profile'):continue
  assert entry['elapsed_ns']>=0
  stages[entry['stage']].append((entry['elapsed_ns']/1e6,row['display_index']))
assert stages
def stats(v):
 a=sorted(x[0] for x in v);return dict(count=len(a),median_ms=statistics.median(a),p95_ms=a[min(len(a)-1,int(len(a)*.95))],max_ms=a[-1],largest=[dict(ms=x,index=i) for x,i in sorted(v,reverse=True)[:5]])
out=dict(result='PASS_CONSUMER_STAGE_TELEMETRY',stages={k:stats(v) for k,v in stages.items()},scope='Recorded consumer CPU wall intervals, includes Python scheduling and driver waits; not GPU completion or visible cadence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
for k,v in out['stages'].items():print(k,{a:b for a,b in v.items() if a!='largest'})
