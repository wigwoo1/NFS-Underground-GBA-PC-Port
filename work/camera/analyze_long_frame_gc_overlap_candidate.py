import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());l=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert l['dropped']==0 and l['total']==len(l['records']);assert r['gc_trace_dropped']==0
ps=r['producer_retention']['long_scene_preparations'];assert ps['dropped']==0
rows=[]
for e in l['records']:
 a=e['begin_ns'];b=a+e['interval_ns'];assert b>a
 overlaps=[]
 for g in r['gc_collection_samples']:
  assert g['start_ns']<=g['end_ns']
  if g['start_ns']<b and g['end_ns']>a:overlaps.append(dict(generation=g['generation'],thread_id=g['thread_id'],overlap_ns=min(b,g['end_ns'])-max(a,g['start_ns'])))
 producers=[dict(refresh=x['refresh'],elapsed_ns=x['ns'],overlap_ns=min(b,x['completed_ns'])-max(a,x['started_ns'])) for x in ps['records'] if x['started_ns']<b and x['completed_ns']>a]
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],interval_ns=e['interval_ns'],parent_gc=overlaps,long_producer=producers))
out=dict(result='PASS_COMPLETE_LONG_INTERVAL_PARENT_GC_OVERLAP',rows=rows,scope='Recorded parent GC only, zero dropped records; excludes child GC and unrecorded scheduler causes. Producer list covers long scene preparations only, not every original update.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(rows),sum(bool(x['parent_gc']) for x in rows))
