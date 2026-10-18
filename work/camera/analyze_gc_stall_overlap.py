"""Measure collection overlap without treating coincidence as exclusive cause."""
import json,sys
from pathlib import Path
def overlap(begin,end,collections):
 spans=sorted((max(begin,x['start_ns']),min(end,x['end_ns'])) for x in collections if min(end,x['end_ns'])>max(begin,x['start_ns']))
 total=0;last=begin
 for a,b in spans:
  total+=max(0,b-max(a,last));last=max(last,b)
 return total/1e6
def analyze(r):
 gc=r['gc_collection_samples'];assert r['gc_trace_dropped']==0
 for x in gc:assert x['end_ns']>=x['start_ns']
 prep=[]
 for x in r['world_preparation_stage_samples']:
  if x['completed_ns']-x['started_ns']>=100000000:
   prep.append(dict(older=x['older'],newer=x['newer'],wall_ms=(x['completed_ns']-x['started_ns'])/1e6,gc_overlap_ms=overlap(x['started_ns'],x['completed_ns'],gc)))
 rows=[x for x in r['presentation_samples'] if x.get('native_commit_stage_ns') and x.get('hidden_window_presented')];device=[]
 for x in rows:
  a=x['native_commit_stage_ns']
  if a[4]-a[3]>=100000000:device.append(dict(display_index=x['display_index'],callback_ms=(a[4]-a[3])/1e6,gc_overlap_ms=overlap(a[3],a[4],gc)))
 return dict(scope='Union of measured GC wall intervals overlapping preparation/native callback wall intervals; overlap is not exclusive CPU or causal proof.',collections=len(gc),max_collection_ms=max(((x['end_ns']-x['start_ns'])/1e6 for x in gc),default=0),preparation_over100ms=prep,callbacks_over100ms=device)
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.gc-overlap.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
