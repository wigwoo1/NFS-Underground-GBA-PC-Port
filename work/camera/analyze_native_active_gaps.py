"""Disjoint native presentation gap phases, with exact source preparation joins."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x.get('native_transaction_candidate')];gaps=[]
for old,new in zip(rows,rows[1:]):
 a=old['native_committed_sample'][6];b=new['native_committed_sample'][6]
 if b-a<=33333333:continue
 if any(p['begin_ns']<b and p['end_ns']>a for p in r['pause_events']):continue
 draw=new['native_draw_boundary']
 # Instrumentation timestamps are collected at Python/native handoff boundaries
 # and can be a few microseconds out of call order. Preserve the total commit
 # interval while recording, rather than silently asserting away, inversions.
 raw=[('sample_begin',new['sample_begin_ns']),('transaction_begin',new['transaction_begin_ns']),('draw_begin',draw[0]),('draw_end',draw[1])]
 points=[a];adjustments=[]
 for name,value in raw:
  bounded=min(b,max(points[-1],value))
  if bounded!=value:adjustments.append(dict(event=name,raw_ns=value,bounded_ns=bounded,delta_ns=bounded-value))
  points.append(bounded)
 points.append(b)
 names=['before_sample','sample_arguments','native_entry','draw','wait_commit']
 phases={name:(end-start)/1e6 for name,start,end in zip(names,points,points[1:])}
 assert abs(sum(phases.values())-(b-a)/1e6)<.001
 identity=[new['epoch'],new['source_older'],new['refresh']]
 stages=[s for s in r['world_preparation_stage_samples'] if (s['older'],s['newer'])==tuple(identity[1:])]
 jobs=[j for j in r['preparation_queue_samples'] if list(j['identity'] or [])==identity]
 updates=[dict(refresh=u['refresh'],overlap_ms=max(0,min(b,u['completed_ns'])-max(a,u['started_ns']))/1e6) for u in r['original_update_samples'] if u['started_ns']<b and u['completed_ns']>a]
 gaps.append(dict(index=new['display_index'],identity=identity,gap_ms=(b-a)/1e6,phases_ms=phases,timestamp_order_adjustments=adjustments,left_ns=a,right_ns=b,pair_begin_ns=new['pair_begin_ns'],pair_ready_ns=new['pair_ready_ns'],preparation_jobs=jobs,process_stages=stages,overlapping_original_updates=updates))
out=dict(active_long_gaps=len(gaps),phase_totals_ms={name:sum(g['phases_ms'][name] for g in gaps) for name in names},timestamp_adjustment_count=sum(len(g['timestamp_order_adjustments']) for g in gaps),largest=sorted(gaps,key=lambda g:g['gap_ms'],reverse=True)[:15],scope='Exact nonpause native commit gaps; disjoint consumer phases after monotonic clamping of instrumentation boundary inversions to the commit interval. Every clamp is retained in timestamp_order_adjustments. Original-update overlaps are concurrent evidence, not additive or exclusive CPU time. Joined preparation identities may include retired generations.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='largest'},indent=2))
