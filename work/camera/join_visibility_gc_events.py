import json,sys
from pathlib import Path
from analyze_gc_stall_overlap import overlap
from analyze_consumer_gap_partition import analyze
r=json.loads(Path(sys.argv[1]).read_text());g=json.loads(Path(sys.argv[2]).read_text());v=json.loads(Path(sys.argv[3]).read_text());assert g['dropped']==v['dropped']==0 and g['policy_unchanged']
collections=g['collections'];rows={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')};parts=analyze(r)
for p in parts['largest']:
 end=rows[p['display_index']]['native_committed_sample'][6];begin=end-round(p['gap_ms']*1e6);p['gc_union_overlap_ms']=overlap(begin,end,collections)
slow=[]
for tid,a in v['records']:
 slow.append(dict(thread_id=tid,count=a[0],wall_ms=(a[10]-a[1])/1e6,gc_any_thread_overlap_ms=overlap(a[1],a[10],collections),gc_same_thread_overlap_ms=overlap(a[1],a[10],[x for x in collections if x['thread_id']==tid])))
out=dict(result='PASS_EVENT_OVERLAP_JOIN',collections=len(collections),max_collection_ms=max(((x['end_ns']-x['start_ns'])/1e6 for x in collections),default=0),visibility_calls=v['completed'],slow_visibility=slow,largest_gaps=parts['largest'],scope='Actual bounded collection intervals; same-thread versus any-thread visibility overlap and disjoint CPU gaps. Correlation only; instrumentation overhead remains; no physical scanout proof.')
Path(sys.argv[4]).write_text(json.dumps(out,indent=2));print(json.dumps({k:val for k,val in out.items() if k!='largest_gaps'},indent=2))
