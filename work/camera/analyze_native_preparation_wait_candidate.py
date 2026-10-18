"""Exact prior-to-draw wait partition with preparation publication associations."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
path=Path(sys.argv[1]);raw=json.loads(path.read_text());baseline=analyze(raw)
events=raw['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records'];requests=raw['world_preparation_stage_samples'];rows=[]
for event in events:
 start=event['begin_ns'];draw=event['caller_timing']['draw_begin_ns'];caller=event['caller_stages'];take=caller['preparation_take_begin_ns'];ready=caller['preparation_take_end_ns']
 assert take<=ready<=draw
 points=[start,max(start,min(draw,take)),max(start,min(draw,ready)),draw];assert points==sorted(points)
 spans=[b-a for a,b in zip(points,points[1:])];assert sum(spans)==draw-start
 publications=[]
 for request in requests:
  for sample in request['parent_sample_rows']:
   stamp=sample['published_ns']
   if take<=stamp<=ready:
    terminal=request['terminal'];child=terminal[5];transfer=next(row for row in child['sample_transfer_rows'] if row['index']==sample['index'])
    publications.append(dict(older=request['older'],newer=request['newer'],generation=request['generation'],sample_index=sample['index'],request_started_ns=request['started_ns'],publication_ns=stamp,child_construct_ms=(child['constructed_ns']-child['child_started_ns'])/1e6,child_prepare_since_ack_ms=transfer['prepare_since_ack_ns']/1e6,request_started_before_take_ms=(take-request['started_ns'])/1e6,publication_to_wait_end_ms=(ready-stamp)/1e6))
 rows.append(dict(identity=[event['epoch'],event['generation'],event['display_index']],commit_gap_ms=event['interval_ns']/1e6,prior_to_draw_ms=(draw-start)/1e6,prior_partition_ms=dict(before_take=spans[0]/1e6,preparation_take_wait=spans[1]/1e6,ready_to_draw=spans[2]/1e6),draw_prepare_ms=(event['caller_timing']['draw_end_ns']-draw)/1e6,publications_during_take=publications))
out=dict(result='PASS_COMPLETE_NATIVE_PREPARATION_WAIT_PARTITION',long_intervals=len(rows),wait_over_10ms=sum(r['prior_partition_ms']['preparation_take_wait']>10 for r in rows),total_wait_ms=sum(r['prior_partition_ms']['preparation_take_wait'] for r in rows),max_wait_ms=max(r['prior_partition_ms']['preparation_take_wait'] for r in rows),rows=rows,scope='Exact partition of all retained >25ms native commit intervals with zero-drop ledger. Request/sample publication timestamps overlap actual preparation take range; association is not exclusive scheduling/CPU cause or source-scene identity proof. No scanout60 claim.')
path.with_name(path.stem+'-preparation-wait-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
for row in sorted(rows,key=lambda r:r['commit_gap_ms'],reverse=True)[:3]:print(row)
