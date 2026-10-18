import sys,json,statistics
from pathlib import Path
def summarize(path):
 r=json.loads(Path(path).read_text());gc=r['gc_collection_samples'];live_begin=min(x['transaction_begin_ns'] for x in r['presentation_samples']);live_end=max(x['transaction_end_ns'] for x in r['presentation_samples']);gc=[g for g in gc if g['start_ns']<live_end and g['end_ns']>live_begin];dur=[(g['end_ns']-g['start_ns'])/1e6 for g in gc if g['generation']==2];gaps=[];previous=None
 for row in r['presentation_samples']:
  if row['native_result']!=1:continue
  if previous and (row['epoch'],row['generation'])==(previous['epoch'],previous['generation']) and row['display_index']==previous['display_index']+1:
   delta=(row['callback_timing']['present_end_ns']-previous['callback_timing']['present_end_ns'])/1e6;assert delta>=0;gaps.append(delta)
  previous=row
 assert gaps
 return dict(report=path,updates=r['original_updates'],successful_presentations=sum(x['native_result']==1 for x in r['presentation_samples']),live_window_begin_ns=live_begin,live_window_end_ns=live_end,full_collections=len(dur),full_collection_max_ms=max(dur,default=0),full_collection_total_ms=sum(dur),present_interval_median_ms=statistics.median(gaps),present_interval_max_ms=max(gaps),over25ms=sum(x>25 for x in gaps),over50ms=sum(x>50 for x in gaps),presentation_encoding=r.get('compact_presentation_diagnostic_stats'),preparation_encoding=r.get('compact_preparation_diagnostic_stats'),retained_producer_rows=len(r['producer_cycle_samples']),retained_submit_rows=len(r['worker_submit_stage_samples']),retained_preparation_queue_rows=len(r['preparation_queue_samples']))
result=dict(baseline=summarize(sys.argv[1]),candidate=summarize(sys.argv[2]),scope='Sequential observed runs; workload/OS scheduling may vary. Compare collection scan cost and encoding overhead, not sole-cause proof or physical scanout certification.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
