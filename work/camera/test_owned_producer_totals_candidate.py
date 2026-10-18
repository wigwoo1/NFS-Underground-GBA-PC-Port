import json
from pathlib import Path
from owned_producer_totals_candidate import ProducerRows
source=json.loads(Path('work/camera/prototype-runs/owned-native-1791502761374205500.json').read_text())['producer_cycle_samples'];v=ProducerRows()
for row in source:v.append(row)
assert v.total_records==len(source) and len(v)<=240
assert v.duration.count==len(source) and v.duration.total==sum(x['ns'] for x in source) and v.duration.maximum==max(x['ns'] for x in source)
for key,stage in v.stages.items():
 values=[x['stages'][key] for x in source if key in x['stages']];assert stage.count==len(values) and stage.total==sum(values) and stage.maximum==max(values)
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791503645918236500.json').read_text());assert r['result']=='SMOKE_COMPLETE' and r['timing']['simulation_with_source_hooks']['count']==r['original_updates']==298
assert r['timing']['simulation_with_source_hooks']['median_ms'] is None and r['producer_retention']['total_records']==r['timing']['producer_read_validate_reconstruct_submit']['count']
assert r['shutdown_evidence']['active_contexts_after_close']==0 and r['shutdown_evidence']['preparation_service_shutdown']['child_exitcode']==0
out=dict(result='PASS_PRODUCER_TOTALS',reference_records=len(source),retention=v.stats(),live_updates=298,scope='Captured full-log exact duration/stage totals with bounded rows; short live simulation count parity. Stages count only present observations, no invented missing zero durations.')
Path('work/camera/prototype-runs/native-producer-totals-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
