"""Require complete slow-update and GC ledgers; correlate without assigning causality."""
import json,sys
from pathlib import Path

def overlap(a,b,events):
 spans=sorted((max(a,g['start_ns']),min(b,g['end_ns'])) for g in events if g['start_ns']<b and g['end_ns']>a)
 total=0;end=a
 for l,h in spans:
  total+=max(0,h-max(l,end));end=max(end,h)
 return total

def analyze(r):
 assert r['result']=='SMOKE_COMPLETE' and r['error'] is None and r['gc_trace_dropped']==0
 retention=r['original_update_retention'];s=retention['slow_original_updates'];totals=retention['whole_run_original_deadlines']
 assert totals['count']==r['original_updates'] and s['dropped']==0
 assert s['total']==totals['completion_over_two_updates']==len(s['records'])
 assert r['pause_retention']['dropped_records']==0
 out=[];seen=set()
 for x in s['records']:
  key=(x['clock_origin'],x['clock_base'],x['refresh']);assert key not in seen;seen.add(key)
  d=x['original_deadline_ns'];a=x['started_ns'];b=x['completed_ns'];n=x['native_boundary']
  assert a<=n[0]<=n[1]<=b and (b-d)*16777216>2*280896*1000000000
  expected=x['clock_origin']+((x['refresh']-x['clock_base']+1)*280896*1000000000+16777215)//16777216
  assert d==expected
  out.append(dict(refresh=x['refresh'],start_residual_ms=(a-d)/1e6,native_ms=(n[1]-n[0])/1e6,post_native_ms=(b-n[1])/1e6,completion_residual_ms=(b-d)/1e6,gc_during_native_ms=overlap(n[0],n[1],r['gc_collection_samples'])/1e6,gc_after_native_ms=overlap(n[1],b,r['gc_collection_samples'])/1e6,gc_deadline_to_start_ms=overlap(d,a,r['gc_collection_samples'])/1e6 if a>d else 0,pause_overlaps_deadline_window=any(p['begin_ns']<b and p['end_ns']>d for p in r['pause_events'])))
 return dict(result='COMPLETE_SLOW_PRODUCER_GC_CORRELATION',count=len(out),post_native_gc_over_10ms=sum(x['gc_after_native_ms']>10 for x in out),native_gc_over_10ms=sum(x['gc_during_native_ms']>10 for x in out),deadline_to_start_gc_over_10ms=sum(x['gc_deadline_to_start_ms']>10 for x in out),pause_windows=sum(x['pause_overlaps_deadline_window'] for x in out),records=out,scope='Exact whole slow-update partition and clipped GC union. Residual windows can overlap; no exclusive causality or pixel cadence proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='records'})
