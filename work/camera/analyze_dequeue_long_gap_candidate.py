"""Complete dequeue evidence for gaps before scene pair entry."""
import json,sys
from pathlib import Path
import statistics
src=Path(sys.argv[1]);r=json.loads(src.read_text());ledger=r['boundary_retention']['complete_dequeues'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
all_rows=ledger['records'];costs=[]
for row in all_rows:
 points=[row[k] for k in ('dequeued_ns','popped_ns','snapshot_ready_ns','copied_ns','matched_ns')];assert points==sorted(points)
 costs.append((row['copied_ns']-row['snapshot_ready_ns'])/1e6)
summary=dict(count=len(costs),mean_ms=statistics.mean(costs),median_ms=statistics.median(costs),p95_ms=sorted(costs)[int((len(costs)-1)*.95)],max_ms=max(costs))
results=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 a=e['begin_ns'];pair=e['caller_stages']['pair_begin_ns']
 if pair<=a:
  results.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],classification='existing_pair_continuation',pair_started_before_interval_ms=(a-pair)/1e6));continue
 matches=[x for x in all_rows if a<=x['matched_ns']<=pair]
 assert len(matches)==1,'Cannot uniquely associate a source dequeue to pair entry'
 row=matches[0];points=[a,row['loop_started_ns'],row['notification_wait_begin_ns'],row['dequeued_ns'],row['popped_ns'],row['snapshot_ready_ns'],row['copied_ns'],row['matched_ns'],pair];assert points==sorted(points)
 names=['prior_commit_to_loop','input_ready','notification_wait','native_pop','snapshot_lookup','frame_equality_or_copy','scene_match','match_to_pair']
 parts={k:(b-a)/1e6 for k,a,b in zip(names,points,points[1:])};assert abs(sum(parts.values())-(pair-e['begin_ns'])/1e6)<1e-9
 results.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],source_refresh=row['refresh'],frame_bytes=row['frame_bytes'],source_submitted_before_prior_commit_ms=(a-row['source_submitted_ns'])/1e6,partition_ms=parts))
out=dict(result='PASS_COMPLETE_DEQUEUE_LONG_GAP_PARTITION',source=str(src.resolve()),complete_dequeues=len(all_rows),frame_equality_or_copy_distribution=summary,rows=results,scope='Unique time-range association from complete scalar ledger; original/native frame equality retained. Scalar walltime cannot distinguish CPU compute, lock scheduling or GIL reacquisition. No physical60fps claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
