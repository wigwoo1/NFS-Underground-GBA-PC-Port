import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
def audit(r):
 analyze(r)
 rows=[]
 for event in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
  c=event['caller_stages'];a=event['begin_ns'];b=event['caller_timing']['draw_begin_ns']
  assert a<=b<=event['end_ns']
  if 'preparation_take_begin_ns' not in c: continue
  points=[a,c['pair_begin_ns'],c['preparation_take_begin_ns'],c['preparation_take_end_ns'],c['pair_ready_ns'],c['slot_begin_ns'],c['sample_end_ns'],c['sky_end_ns'],c['owner_end_ns'],c['lock_acquired_ns'],b]
  clipped=[max(a,min(b,x)) for x in points];assert clipped==sorted(clipped)
  spans=[y-x for x,y in zip(clipped,clipped[1:])];assert sum(spans)==b-a
  commit=event['transaction']['commit'];matches=[x for x in r['world_preparation_stage_samples'] if x['parent_sample_rows'] and x['older']==commit[2] and x['newer']==commit[3] and x['terminal'][5]['history_identity']==[commit[0],commit[3]]]
  assert len(matches)==1,(commit,len(matches))
  request=matches[0];diag=request['terminal'][5];first=request['parent_sample_rows'][0];child=diag['sample_transfer_rows'][0]
  assert first['received_ns']<=first['decoded_ns']<=first['publication_begin_ns']<=first['published_ns']
  rows.append(dict(identity=commit[:5],interval_ms=event['interval_ns']/1e6,prior_to_draw_ms=(b-a)/1e6,partition_ms=[x/1e6 for x in spans],take_elapsed_ms=(c['preparation_take_end_ns']-c['preparation_take_begin_ns'])/1e6,request_started_ns=request['started_ns'],first_published_ns=first['published_ns'],child_first_prepare_ms=child['prepare_since_ack_ns']/1e6,first_publish_to_take_return_ms=(c['preparation_take_end_ns']-first['published_ns'])/1e6,request_first_pipeline_ms=(first['published_ns']-request['started_ns'])/1e6))
 return dict(result='PASS_LONG_INTERVAL_PRE_DRAW_REQUEST_ACCOUNTING',phase_order=['before_pair','pair_to_take','preparation_take','take_to_pair_ready','pair_to_slot','sample','sky','owner','lock','lock_to_draw'],rows=sorted(rows,key=lambda x:x['interval_ms'],reverse=True),scope='Exact elapsed partitions and unique source-request association; not exclusive CPU or cause proof.')
if __name__=='__main__':
 out=audit(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
