import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
def stats(values):
 values=list(values)
 return dict(count=len(values),median_ms=statistics.median(values)/1e6,min_ms=min(values)/1e6,max_ms=max(values)/1e6) if values else dict(count=0)
b=r['consumer_boundary_stage_samples'];p=r['preparation_queue_samples'];rows=[x for x in r['presentation_samples'] if x.get('native_result')==1]
prep={(x['identity'][0],x['identity'][2]):x for x in p if x.get('finished_ns')}
matched=[(x,prep[(r['epoch'],x['refresh'])]) for x in b if (r.get('epoch'),x['refresh']) in prep]
# Header epochs need not be report-level: retained presentation rows supply identity.
if not matched:
 epochs={x['epoch'] for x in rows}
 matched=[(x,prep[(e,x['refresh'])]) for x in b for e in epochs if (e,x['refresh']) in prep]
wait=[x['dequeued_ns']-x['source_submitted_ns'] for x in b]
lead=[x['dequeued_ns']-q['finished_ns'] for x,q in matched]
draw=[x['callback_timing']['draw_end_ns']-x['callback_timing']['draw_begin_ns'] for x in rows]
present=[x['callback_timing']['present_end_ns']-x['callback_timing']['present_begin_ns'] for x in rows]
late=[x['transaction_end_ns']-x['presentation_deadline_ns'] for x in rows]
stages={}
for row in rows:
 for stage in (row.get('prepared') or {}).get('consumer_stages',[]):stages.setdefault(stage['stage'],[]).append(stage['elapsed_ns'])
out=dict(result='RETAINED_QUEUE_THROUGHPUT_ANALYZED',source_queue_wait=stats(wait),preparation_lead_at_dequeue=stats(lead),preparation_ready_before_dequeue=sum(v>=0 for v in lead),draw_callback=stats(draw),present_callback=stats(present),deadline_lateness=stats(late),first_last_retained_lateness_ms=[late[0]/1e6,late[-1]/1e6],consumer_stages={k:stats(v) for k,v in stages.items()},scope='Retained60 source boundaries/preparation jobs and120 presentation samples only; callbacks include cross-thread dispatch/wait. Preparation-ready-at-dequeue does not rule out earlier delays. No whole-run growth or causal classification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
