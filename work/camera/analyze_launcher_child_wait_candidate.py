"""Conservative completed-request temporal association for launcher Future waits."""
import json,sys
from pathlib import Path
def analyze(r):
 ledger=r['preparation_retention']['slow_process_intervals']
 assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
 events=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
 assert events['dropped']==0 and events['total']==len(events['records'])
 rows=[]
 for e in events['records']:
  c=e['caller_stages'];a=c['preparation_take_begin_ns'];b=c['preparation_take_end_ns']
  assert b>=a
  if b-a<1000000:continue
  matches=[q for q in ledger['records'] if a<=q['end_ns']<=b and q['parent_received_ns']<=b]
  row=dict(index=e['display_index'],wait_ms=(b-a)/1e6,completed_temporal_matches=len(matches))
  if len(matches)==1:
   q=matches[0];t=q['child_boundaries'];stamps=[t[k] for k in ('started_ns','decoded_ns','initialized_ns','constructed_ns','sampled_ns','encoded_ns','sent_ns')]
   assert stamps==sorted(stamps) and q['child_gc_dropped']==0
   row.update(older=q['older'],newer=q['newer'],child_construct_ms=q['child_construct_ns']/1e6,child_precompute_ms=q['child_precompute_ns']/1e6,child_send_ms=q['child_send_ns']/1e6,parent_decode_ms=q['parent_output_decode_ns']/1e6,construct_stages=q['construct_stages'],sample_stages=q['sample_stages'],child_gc=q['child_gc_rows'])
  rows.append(row)
 return dict(result='COMPLETE_TEMPORAL_CHILD_WAIT_ASSOCIATION',rows=rows,scope='Completed request inside Future wait with complete retained slow ledger; association only, pair identity is not stored in these API gap rows. Multiple or absent candidates remain unresolved; no exclusive causal or scanout proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
 print([(x['index'],x['wait_ms'],x['completed_temporal_matches'],x.get('child_precompute_ms')) for x in out['rows']])
