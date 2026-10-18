import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for gap in ledger['records']:
 c=gap['caller_stages'];a=gap['begin_ns'];b=gap['end_ns']
 stamps=[c[k] for k in ['slot_begin_ns','sample_end_ns','sky_begin_ns','sky_end_ns','owner_begin_ns','owner_end_ns','lock_begin_ns','lock_acquired_ns']]
 assert all(x<=y for x,y in zip(stamps,stamps[1:]))
 boundaries=[a]+[min(b,max(a,x)) for x in stamps]+[b]
 names=['before_slot','sample','sample_to_sky','sky','sky_to_owner','owner','owner_to_lock','publication_lock_wait','transaction']
 values={name:(y-x)/1e6 for name,x,y in zip(names,boundaries,boundaries[1:])}
 assert sum(y-x for x,y in zip(boundaries,boundaries[1:]))==gap['interval_ns']
 ready=c['pair_ready_ns'];assert c['pair_begin_ns']<=ready<=c['slot_begin_ns']
 values['setup_overlap_ms']=max(0,min(b,ready)-max(a,c['pair_begin_ns']))/1e6
 rows.append(dict(display_index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,**values))
out=dict(result='PASS_COMPLETE_CALLER_INTERVAL_PARTITION',long_intervals=len(rows),rows=rows,scope='Exact partition clipped to each actual presentation interval; before_slot can include waits and scheduling. Setup overlap is a separate interval intersection, not additive or exclusive CPU. No visible60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
