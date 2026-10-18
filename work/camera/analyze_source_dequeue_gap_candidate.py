"""Exact source dequeue partition of clean native commit gaps."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);r=json.loads(p.read_text());analyze(r)
ledger=r['boundary_retention']['complete_dequeues'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
producer=r['producer_retention']['long_scene_preparations'];assert producer['dropped']==0 and producer['total']==len(producer['records'])
rows=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 start=e['begin_ns'];c=e['caller_stages'];pair=c['pair_begin_ns'];take=max(start,c['preparation_take_begin_ns']);refresh=e['transaction']['commit'][3]
 matches=[x for x in ledger['records'] if x['refresh']==refresh and x['matched_ns']<=pair];assert matches
 b=max(matches,key=lambda x:x['matched_ns'])
 raw=[start,b['loop_started_ns'],b['notification_wait_begin_ns'],b['dequeued_ns'],b['popped_ns'],b['snapshot_ready_ns'],b['copied_ns'],b['matched_ns'],pair,take]
 clipped=[max(start,min(take,t)) for t in raw];assert clipped==sorted(clipped),(refresh,raw)
 durations=[(v-u)/1e6 for u,v in zip(clipped,clipped[1:])];assert abs(sum(durations)-(take-start)/1e6)<1e-8
 names=['before_consumer_loop','loop_to_wait','notification_wait','pop','snapshot','frame_match','scene_match','match_to_pair','claim_and_prefetch_submit']
 submitted=b['source_submitted_ns'];wait_start=max(start,min(take,b['notification_wait_begin_ns']));wait_end=max(start,min(take,b['dequeued_ns']));available=max(wait_start,min(wait_end,submitted))
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],source_newer=refresh,gap_ms=e['interval_ns']/1e6,before_take_ms=(take-start)/1e6,partition_ms=dict(zip(names,durations)),notification_before_source_submission_ms=(available-wait_start)/1e6,notification_after_source_submission_ms=(wait_end-available)/1e6,source_submission_relative_prior_commit_ms=(submitted-start)/1e6,producer_long_rows=[x for x in producer['records'] if x['refresh']==refresh],scope='Exact matched refresh and preceding dequeue timestamps; notification-before-submission elapsed range is not exclusive producer CPU causation.'))
out=dict(result='PASS_COMPLETE_SOURCE_DEQUEUE_GAP_PARTITION',rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='All retained native >25ms gaps and complete zero-drop dequeue/slow-producer ledgers; clipped exact partition, repeated pair stages may precede interval. Missing ordinary producer rows cannot prove exclusive cause.')
p.with_name(p.stem+'-source-dequeue-gap-audit.json').write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps([{k:v for k,v in x.items() if k!='producer_long_rows'} for x in out['rows'][:3]],indent=2))
