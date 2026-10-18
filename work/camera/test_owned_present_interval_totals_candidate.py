import json
from pathlib import Path
from owned_validated_bounded_diagnostics_candidate import ValidatedPresentationDiagnostics
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791502761374205500.json').read_text());v=ValidatedPresentationDiagnostics(r['producer_thread_id'],0,max_records=3,max_bytes=65536)
for row in r['presentation_samples']:v.append(row)
a=v.finalize()['whole_run_present_intervals'];assert a==v.finalize()['whole_run_present_intervals']
rows=[x for x in r['presentation_samples'] if x['native_result']==1];gaps=[];excluded=0
for old,new in zip(rows,rows[1:]):
 if (old['epoch'],old['generation'])==(new['epoch'],new['generation']) and new['display_index']==old['display_index']+1:gaps.append(new['callback_timing']['present_end_ns']-old['callback_timing']['present_end_ns'])
 else:excluded+=1
assert a['adjacent_successful_intervals']==len(gaps) and a['excluded_discontinuities']==excluded
assert a['max_ms']==max(gaps)/1e6 and a['mean_ms']==sum(gaps)/len(gaps)/1e6
for key,predicate in [('over_25ms',lambda x:x>25000000),('over_33_333ms',lambda x:x*3>100000000),('over_50ms',lambda x:x>50000000),('under_8ms',lambda x:x<8000000)]:assert a[key]==sum(predicate(x) for x in gaps)
out=dict(result='PASS_STREAMING_INTERVAL_PARITY',intervals=a,retained_records=len(v),scope='Exact complete captured report reference parity and repeatable finalization; actual live aggregate verification pending.')
Path('work/camera/prototype-runs/native-streaming-interval-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
