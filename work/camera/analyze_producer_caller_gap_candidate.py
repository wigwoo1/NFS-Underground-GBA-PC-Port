"""Complete slow-update preceding-caller partition; retain pauses and GC."""
import json,sys,statistics
from pathlib import Path
from analyze_slow_producer_gc_candidate import analyze,overlap
r=json.loads(Path(sys.argv[1]).read_text());base=analyze(r);rows=r['original_update_retention']['slow_original_updates']['records'];out=[]
for x in rows:
 c=x.get('preceding_caller');assert c,'Initial slow update lacks preceding boundary'
 p=c['previous_completed_ns'];a=c['submit_begin_ns'];b=c['submit_end_ns'];end=x['started_ns']
 assert p<=a<=b<=end
 parts=dict(before_submit_ms=(a-p)/1e6,submit_ms=(b-a)/1e6,after_submit_ms=(end-b)/1e6,total_ms=(end-p)/1e6)
 assert abs(sum(parts[k] for k in ('before_submit_ms','submit_ms','after_submit_ms'))-parts['total_ms'])<1e-6
 parts.update(refresh=x['refresh'],gc_submit_ms=overlap(a,b,r['gc_collection_samples'])/1e6,gc_caller_ms=overlap(p,end,r['gc_collection_samples'])/1e6,pause_overlap=any(v['begin_ns']<end and v['end_ns']>p for v in r['pause_events']))
 out.append(parts)
low=[x for x in out if x['gc_caller_ms']<=2 and not x['pause_overlap']]
result=dict(result='COMPLETE_SLOW_UPDATE_PRECEDING_CALLER_PARTITION',count=len(out),low_gc_unpaused_count=len(low),low_gc_medians_ms={k:statistics.median(x[k] for x in low) for k in ('before_submit_ms','submit_ms','after_submit_ms','total_ms')} if low else {},records=out,scope='Preceding interval of every slow update, including wait/pause; adjacent windows and residuals are not independent lost time. Native graphics and logic unchanged.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='records'})
