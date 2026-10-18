import json,sys,statistics
from pathlib import Path
source,out=map(Path,sys.argv[1:3]);d=json.loads(source.read_text());assert d['dropped']==0
pairs={}
for r in d['rows']:
 assert r[2] in (0,1) and r[3]<=r[4] and r[5]>0
 pairs.setdefault((r[0],r[1]),{})[r[2]]=r
assert all(set(v)=={0,1} for v in pairs.values())
periods=[r[7]*1000/r[5] for r in d['rows'] if r[6]==0 and r[7]]
cost=[(r[4]-r[3])*1000/r[5] for r in d['rows']]
joined=[]
for key,v in pairs.items():
 a,b=v[0],v[1];assert a[4]<=b[3] and a[21]==b[21] and a[21] in (0,1)
 joined.append(dict(identity=key,swap_bracket_ms=(b[3]-a[4])*1000/a[5],composition_refresh_delta=b[11]-a[11],composition_frame_delta=b[12]-a[12]))
r=dict(result='PASS_READ_ONLY_COMPOSITION_SWAP_BRACKETS',swaps=len(pairs),swap_intervals=sorted(set(x[21] for x in d['rows'])),oml_available_records=sum(x[16]!=0 for x in d['rows']),oml_success_records=sum(x[17]!=0 for x in d['rows']),dwm_success_records=sum(x[6]==0 for x in d['rows']),refresh_period_median_ms=statistics.median(periods),probe_cost_median_ms=statistics.median(cost),probe_cost_max_ms=max(cost),probe_cost_total_ms=sum(cost),swap_bracket_median_ms=statistics.median(x['swap_bracket_ms'] for x in joined),swap_bracket_max_ms=max(x['swap_bracket_ms'] for x in joined),top_swaps=sorted(joined,key=lambda x:x['swap_bracket_ms'],reverse=True)[:10],scope='Bracket excludes composition API calls but includes minimal callback timing between probes. Composition counters are not exact application frame/physical scanout evidence; no exclusive wait causality claim.')
out.write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
