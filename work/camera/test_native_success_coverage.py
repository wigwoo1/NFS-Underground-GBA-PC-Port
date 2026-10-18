import json,copy
from pathlib import Path
from owned_native_transaction_interval_totals_candidate import LongIntervalTotals
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791634635935718400.json').read_text())
rows=r['presentation_samples'];assert len(rows)==5
tracker=LongIntervalTotals()
for row in rows:tracker.observe(row)
missed=json.loads(Path('work/camera/prototype-runs/expired-admission-1791634636153856000.json').read_text())
begin=min(row['native_transaction']['wait'][1] for row in rows);end=max(x['native'][5] for x in missed['records'])
a=tracker.coverage(begin,end);assert a['successful_samples']==5 and a['trailing_hold_ns']>10000000000
assert copy.copy(tracker).coverage(begin,end)==a
empty=LongIntervalTotals().coverage(10,100);assert empty['successful_samples']==0 and empty['initial_hold_ns']==empty['trailing_hold_ns']==90 and not empty['qualified']
for bounds in [(end,begin),(-1,end),(begin,0),(tracker.first_success_ns+1,end)]:
 try:tracker.coverage(*bounds)
 except ValueError:pass
 else:raise AssertionError('Invalid coverage accepted')
out=dict(result='PASS_ACTUAL_STARVATION_BOUNDARY_COVERAGE',coverage=a,scope='Complete five successful frames and504retirement rows from actualfailedrun; end is last retirement, lower bound for further idle. No live extended tracker or scanout qualification.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/native-coverage-replay.json').write_text(json.dumps(out,indent=2));print(out)
