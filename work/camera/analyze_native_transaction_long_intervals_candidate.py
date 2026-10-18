import json,sys
from pathlib import Path
def analyze(r):
 assert r['result']=='SMOKE_COMPLETE' and r['error'] is None and r['gc_trace_dropped']==0
 stats=r['bounded_diagnostic_stats']['whole_run_api_intervals'];summary=stats['native_commit_intervals'];ledger=stats['native_commit_long_intervals']
 assert ledger['dropped']==0 and ledger['total']==summary['over25']==len(ledger['records'])
 assert ledger['capacity']==512 and ledger['record_byte_limit']==16384
 keys=set();rows=[]
 for event in ledger['records']:
  a,b=event['begin_ns'],event['end_ns'];delta=b-a;assert delta==event['interval_ns'] and delta>25000000
  key=(event['epoch'],event['generation'],event['display_index']);assert key not in keys;keys.add(key)
  tx=event['transaction'];st=tx['stages'];ps=tx['presentation']['present_stage_ns'];wait=tx['wait']
  assert tx['native_result']==1 and tx['native_callback_count']==1 and tx['native_batch_result']==0
  assert tx['commit'][:2]==list(key[:2]) and tx['commit'][4]==key[2] and tx['commit'][6]==b
  assert wait[2]>=wait[1] and wait[0]<=wait[2]<=st[0]<=st[3]<=ps['begin']<=ps['pumped']<=ps['presented']<=ps['queried']<=st[4]<=b
  dispatch=tx['renderer_dispatch'];assert dispatch['kind']=='commit_present'
  # Clip phase boundaries to this actual commit interval; never double count.
  boundaries=[a,event['caller_timing']['draw_begin_ns'],event['caller_timing']['draw_end_ns'],dispatch['submitted_ns'],dispatch['started_ns'],wait[0],wait[2],ps['begin'],ps['pumped'],ps['presented'],ps['queried'],b]
  clipped=[max(a,min(b,x)) for x in boundaries];assert clipped==sorted(clipped)
  spans=[y-x for x,y in zip(clipped,clipped[1:])];assert sum(spans)==delta
  overlap=[dict(generation=g['generation'],duration_ms=(g['end_ns']-g['start_ns'])/1e6,overlap_ms=(min(b,g['end_ns'])-max(a,g['start_ns']))/1e6) for g in r['gc_collection_samples'] if max(a,g['start_ns'])<min(b,g['end_ns'])]
  rows.append(dict(identity=list(key),interval_ms=delta/1e6,partition_ms=[x/1e6 for x in spans],gc_intersections=overlap))
 assert sum(e['interval_ns']*3>100000000 for e in ledger['records'])==summary['over33']
 assert sum(e['interval_ns']>50000000 for e in ledger['records'])==summary['over50']
 return dict(result='PASS_COMPLETE_NATIVE_COMMIT_LONG_INTERVAL_LEDGER',summary=summary,phase_order=['prior_to_draw','prepare','prepare_to_submit','dispatch_wait','native_entry','deadline_wait','wait_to_present','window_pump','native_present','stats','stats_to_commit'],rows=rows,scope='Complete bounded native commit gaps and clipped exact partition; GC intersection is association, not exclusive cause; no visible pixel/scanout60 proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(out['summary'])
