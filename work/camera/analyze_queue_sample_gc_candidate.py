"""Correlate complete retained child sample intervals and queue-related waits with GC."""
import json,sys
from pathlib import Path
def analyze(r):
 qs=r['world_preparation_stage_samples'];events=[];seen=set();slow=[]
 for q in qs:
  c=q['terminal'][5];g=c['child_gc_trace'];assert g and g['dropped']==0
  for e in g['rows']:
   key=(e['thread'],e['generation'],e['start_ns'],e['end_ns']);assert key not in seen and e['start_ns']<=e['end_ns'];seen.add(key);events.append(e)
 def overlaps(a,b):
  return [dict(generation=e['generation'],duration_ms=(e['end_ns']-e['start_ns'])/1e6,overlap_ms=(min(b,e['end_ns'])-max(a,e['start_ns']))/1e6) for e in events if max(a,e['start_ns'])<min(b,e['end_ns'])]
 for q in qs:
  c=q['terminal'][5]
  for x in c['sample_transfer_rows']:
   end=x['ready_ns'];start=end-x['prepare_since_ack_ns'];assert start<=end
   if x['prepare_since_ack_ns']>20000000:slow.append(dict(pair=[q['older'],q['newer']],sample_index=x['index'],prepare_ms=(end-start)/1e6,gc=overlaps(start,end)))
 ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
 waits=[]
 for e in ledger['records']:
  a,b=e['caller_stages']['preparation_take_begin_ns'],e['caller_stages']['preparation_take_end_ns'];assert a<=b
  waits.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],wait_ms=(b-a)/1e6,child_gc_during_parent_wait=overlaps(a,b)))
 return dict(result='PASS_RETAINED_QUEUE_SAMPLE_GC_CORRELATION',requests=len(qs),unique_events=len(events),slow_samples=slow,waits=waits,scope='Completed zero-drop child GC snapshots and every retained sample preparation interval; GC overlap is temporal association, not exclusive cause. No physical scanout or smooth60 proof.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=analyze(r)
 from copy import deepcopy
 bad=deepcopy(r);q=next(q for q in bad['world_preparation_stage_samples'] if q['terminal'][5]['child_gc_trace']['rows']);g=q['terminal'][5]['child_gc_trace'];g['rows'].append(g['rows'][0])
 try:analyze(bad)
 except AssertionError:pass
 else:raise AssertionError('Duplicate GC accepted')
 out['negative_control_rejected']=True;Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['unique_events']);print(out['waits'])
