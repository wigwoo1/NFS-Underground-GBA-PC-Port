import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for gap in ledger['records']:
 d=gap['renderer_dispatch'];submit=d['submitted_ns'];start=d['started_ns'];previous=d['previous_job_completed_ns']
 points=[previous if previous is not None else min(submit,d['poll_begin_ns']),d['poll_begin_ns'],d['poll_end_ns'],d['dequeue_begin_ns'],d['dequeued_ns'],start]
 assert all(a<=b for a,b in zip(points,points[1:]))
 boundaries=[submit]+[max(submit,x) for x in points]+[start]
 assert all(a<=b for a,b in zip(boundaries,boundaries[1:]))
 names=['before_previous_job_completed','completion_to_poll','input_poll','poll_to_dequeue','dequeue_wait','dequeue_to_dispatch','after_dispatch']
 values={name:(b-a)/1e6 for name,a,b in zip(names,boundaries,boundaries[1:])}
 assert sum(b-a for a,b in zip(boundaries,boundaries[1:]))==start-submit
 gc_overlap=sum(max(0,min(start,g['end_ns'])-max(submit,g['start_ns'])) for g in r['gc_collection_samples'])
 rows.append(dict(display_index=gap['display_index'],queue_ms=(start-submit)/1e6,gc_overlap_ms=gc_overlap/1e6,**values))
out=dict(result='PASS_RENDERER_DEQUEUE_PARTITION',long_intervals=len(rows),largest=sorted(rows,key=lambda x:x['queue_ms'],reverse=True),scope='Exact chronological partition of submission-to-dispatch elapsed. Dequeue wait includes blocking, scheduling and GIL; does not prove queue contention or exclusive CPU. Complete long-interval ledger only.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
