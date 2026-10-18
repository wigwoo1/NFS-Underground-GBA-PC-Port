import json,copy
from pathlib import Path
from owned_present_gap_trace_candidate import PresentationIntervalTotals
from owned_present_interval_totals_candidate import PresentationIntervalTotals as Base
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791505900330501200.json').read_text());candidate=PresentationIntervalTotals();reference=Base();expected=[];previous=None
for row in r['presentation_samples']:
 candidate.observe(row);reference.observe(row)
 if row['native_result']!=1:continue
 key=(row['epoch'],row['generation'],row['display_index']);at=row['callback_timing']['present_end_ns']
 if previous:
  prior,start=previous
  if key[:2]==prior[:2] and key[2]==prior[2]+1 and at-start>25000000:expected.append(dict(start_ns=start,end_ns=at,display_index=key[2],epoch=key[0],generation=key[1]))
 previous=(key,at)
actual=candidate.stats();assert {k:actual[k] for k in reference.stats()}==reference.stats();assert [{k:x[k] for k in ('start_ns','end_ns','display_index','epoch','generation')} for x in actual['slow_gap_samples']]==expected[-256:];assert actual['slow_gap_dropped']==max(0,len(expected)-256)
lookup={(x['epoch'],x['generation'],x['display_index']):x for x in r['presentation_samples'] if x['native_result']==1}
for gap in actual['slow_gap_samples']:
 row=lookup[(gap['epoch'],gap['generation'],gap['display_index'])];timing=row['callback_timing'];prepared=row.get('prepared',{})
 assert gap['stage_cost_ns']=={x['stage']:x['elapsed_ns'] for x in prepared.get('consumer_stages',[])}
 assert gap['source_prepare_ns']==prepared.get('source_prepare_ns')
 assert gap['draw_ns']==timing['draw_end_ns']-timing['draw_begin_ns']
 assert gap['present_ns']==timing['present_end_ns']-timing['present_begin_ns']
 assert gap['prior_return_to_transaction_ns']==row['transaction_begin_ns']-gap['start_ns']
fork=copy.copy(candidate);fork.gaps.clear();assert candidate.stats()==actual
# Force more than the timestamp budget without modifying original rows.
synthetic=PresentationIntervalTotals()
for i in range(301):
 at=i*30000000;synthetic.observe(dict(native_result=1,epoch=1,generation=1,display_index=i,callback_timing=dict(present_begin_ns=at,present_end_ns=at),transaction_end_ns=at))
assert synthetic.stats()['over_25ms']==300 and len(synthetic.gaps)==256 and synthetic.gaps_dropped==44
out=dict(result='PASS_FULL_CAPTURE_GAP_TIMESTAMPS_AND_BUDGET',rows=len(r['presentation_samples']),gaps=len(expected),retention=256,scope='API intervals only; no scanout evidence.')
Path('work/camera/prototype-runs/native-gap-trace-replay-20261008.json').write_text(json.dumps(out,indent=2));print(out)
