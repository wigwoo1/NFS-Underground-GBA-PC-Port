import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());t=json.loads(Path(sys.argv[2]).read_text());assert t['dropped']==0
rows={};retired=0
for a in t['rows']:
 assert len(a)==14
 if a[12]!=1:retired+=1;continue
 key=(a[0],a[1],a[4]);assert key not in rows;rows[key]=a
 assert a[6]<=a[7]<=a[8]<=a[9]<=a[10]<=a[11] and a[13]>0
checks=[]
for s in r['presentation_samples']:
 if s.get('presentation_backend')!='dxgi_flip_sequential':continue
 a=rows.pop((s['epoch'],s['generation'],s['display_index']))
 assert a[2]==s['source_older'] and a[3]==s['refresh'] and a[5]==s['presentation_deadline_ns']
 assert a[8]<=s['sample_begin_ns']<=s['draw_complete_ns']<=a[9]
 assert a[10]<=s['native_committed_sample'][6]<=a[11]
 checks.append(dict(index=a[4],epoch=a[0],availability_ms=(a[8]-a[7])/1e6,initialize_ms=(a[7]-a[6])/1e6,draw_ms=(a[9]-a[8])/1e6,deadline_wait_ms=(a[10]-a[9])/1e6,commit_ms=(a[11]-a[10])/1e6,begin_lateness_ms=(a[6]-a[5])/1e6,availability_end_lateness_ms=(a[8]-a[5])/1e6,end_lateness_ms=(a[11]-a[5])/1e6,polls=a[13]))
assert checks and not rows
summary={k:dict(median=statistics.median(x[k] for x in checks),maximum=max(x[k] for x in checks),first120_median=statistics.median(x[k] for x in checks[:120]),last120_median=statistics.median(x[k] for x in checks[-120:])) for k in ['availability_ms','initialize_ms','draw_ms','deadline_wait_ms','commit_ms','begin_lateness_ms','end_lateness_ms']}
out=dict(result='PASS_EXACT_AVAILABILITY_TRANSACTION_JOIN',checked=len(checks),retired=retired,summary=summary,rows=checks,scope='Exact epoch/generation/display-index/deadline joins with draw/commit containment. Wall intervals include scheduler time. No causal or physical60fps claim.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
