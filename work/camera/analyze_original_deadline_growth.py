"""Disjoint serial producer intervals explain captured deadline lateness growth."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());updates=r['original_update_samples'];captures=r['producer_cycle_samples'];submits=r['worker_submit_stage_samples'];rows=[]
for current,next_update in zip(updates,updates[1:]):
 if current['clock_origin']!=next_update['clock_origin']:continue
 start,end=current['started_ns'],next_update['started_ns'];boundary=current['native_boundary']
 assert start<=boundary[0]<=boundary[1]<=current['completed_ns']<=end
 source=[c for c in captures if c['started_ns']<end and c['completed_ns']>start]
 capture_ns=0;last=current['completed_ns']
 for c in sorted(source,key=lambda c:c['started_ns']):
  a,b=max(start,c['started_ns']),min(end,c['completed_ns']);assert a>=last,'Producer intervals overlap'
  capture_ns+=b-a;last=b
 native_ns=boundary[1]-boundary[0];wrapper_ns=current['completed_ns']-start-native_ns
 remaining=end-start-native_ns-wrapper_ns-capture_ns;assert remaining>=0
 step=next_update['original_deadline_ns']-current['original_deadline_ns']
 growth=(end-next_update['original_deadline_ns'])-(start-current['original_deadline_ns'])
 assert native_ns+wrapper_ns+capture_ns+remaining-step==growth
 related=[s for s in submits if s['submit_begin_ns']<end and s['submit_end_ns']>start]
 rows.append(dict(refresh=current['refresh'],next_refresh=next_update['refresh'],growth_ms=growth/1e6,native_ms=native_ns/1e6,wrapper_ms=wrapper_ns/1e6,capture_ms=capture_ns/1e6,remaining_gate_and_uninstrumented_ms=remaining/1e6,original_step_ms=step/1e6,captures=source,submits=related))
out=dict(checked_intervals=len(rows),excluded_origin_transitions=len(updates)-1-len(rows),sum_growth_ms=sum(x['growth_ms'] for x in rows),totals_ms={k:sum(x[k] for x in rows) for k in ['native_ms','wrapper_ms','capture_ms','remaining_gate_and_uninstrumented_ms']},largest_growth=sorted(rows,key=lambda x:x['growth_ms'],reverse=True)[:12],scope='Serial producer host-clock partition; remaining includes intentional pacing/control polling/uninstrumented waits, not exclusive scheduling. Inner capture/submission stages may nest and are not added to outer totals.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='largest_growth'},indent=2));print(json.dumps([{k:v for k,v in x.items() if k not in ['captures','submits']} for x in out['largest_growth'][:4]],indent=2))
