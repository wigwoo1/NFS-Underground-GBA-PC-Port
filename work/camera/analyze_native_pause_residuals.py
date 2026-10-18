"""Partition pause-crossing native commit gaps after subtracting recorded pause overlap."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x.get('native_transaction_candidate')];out=[]
def active_ns(a,b):
 pauses=sorted((max(a,p['begin_ns']),min(b,p['end_ns'])) for p in r['pause_events'] if p['begin_ns']<b and p['end_ns']>a)
 covered=0;end=a
 for start,stop in pauses:
  covered+=max(0,stop-max(start,end));end=max(end,stop)
 return b-a-covered
for old,new in zip(rows,rows[1:]):
 a=old['native_committed_sample'][6];b=new['native_committed_sample'][6]
 if active_ns(a,b)==b-a:continue
 draw=new['native_draw_boundary'];points=[a,max(a,new['sample_begin_ns']),max(a,new['transaction_begin_ns']),max(a,draw[0]),max(a,draw[1]),b]
 assert points==sorted(points)
 names=['prior_commit_to_sample','sample_and_context','native_entry','native_draw','wait_and_commit'];phases={name:active_ns(start,end)/1e6 for name,start,end in zip(names,points,points[1:])};residual=active_ns(a,b)/1e6;assert abs(sum(phases.values())-residual)<.001
 out.append(dict(index=new['display_index'],raw_gap_ms=(b-a)/1e6,recorded_pause_ms=((b-a)-active_ns(a,b))/1e6,residual_ms=residual,active_phases_ms=phases,pair_begin_ns=new['pair_begin_ns'],pair_ready_ns=new['pair_ready_ns'],left_commit_ns=a,right_commit_ns=b,source_older=new['source_older'],source_newer=new['refresh']))
result=dict(checked_pause_crossings=len(out),largest=sorted(out,key=lambda x:x['residual_ms'],reverse=True),scope='Subtract recorded intentional pause intervals from disjoint native commit-gap phases. Pause entry/exit and preparation outside recorded interval remain residual; no scanout certification.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
