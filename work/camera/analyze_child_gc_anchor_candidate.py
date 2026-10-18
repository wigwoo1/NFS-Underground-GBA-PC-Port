"""GC/anchor time intersections from complete bounded slow-request evidence."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
events={};anchors=[]
for request in ledger['records']:
 assert request['child_gc_dropped']==0
 for g in request['child_gc_rows']:
  assert g['start_ns']<=g['end_ns'];key=(g['start_ns'],g['end_ns'],g['thread_id'])
  if key in events:assert events[key]==g
  events[key]=g
 for sample in request['sample_stages']:
  for stage in sample['stages']:
   if stage['name']!='model_anchors':continue
   overlaps=[dict(generation=g['generation'],elapsed_ms=max(0,min(stage['completed_ns'],g['end_ns'])-max(stage['started_ns'],g['start_ns']))/1e6) for g in request['child_gc_rows'] if stage['started_ns']<g['end_ns'] and stage['completed_ns']>g['start_ns']]
   anchors.append(dict(older=request['older'],newer=request['newer'],alpha=sample['alpha'],anchor_ms=stage['wall_ns']/1e6,gc_overlap_ms=sum(x['elapsed_ms'] for x in overlaps),gc=overlaps))
by_generation={}
for g in events.values():
 entry=by_generation.setdefault(str(g['generation']),dict(count=0,total_ms=0,max_ms=0));elapsed=(g['end_ns']-g['start_ns'])/1e6;entry['count']+=1;entry['total_ms']+=elapsed;entry['max_ms']=max(entry['max_ms'],elapsed)
out=dict(result='PASS_CHILD_GC_ANCHOR_INTERSECTIONS',slow_requests=ledger['total'],unique_gc_events=len(events),by_generation=by_generation,largest_anchors=sorted(anchors,key=lambda x:x['anchor_ms'],reverse=True)[:20],scope='Only complete retained slow requests and selected sample stages; not whole-child GC coverage. Exact time intersection, not proof of exclusive causation or cross-run performance gain.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(by_generation=by_generation,largest_anchors=out['largest_anchors'][:3]),indent=2))
