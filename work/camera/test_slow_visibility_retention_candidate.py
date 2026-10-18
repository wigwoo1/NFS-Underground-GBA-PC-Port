import json,copy
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
raw=json.loads(Path('work/camera/prototype-runs/owned-native-1791553291944588400.json').read_text())
rows=raw['world_preparation_stage_samples']
ledger=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=4096)
for row in rows:ledger.append(row)
stats=ledger.stats()['slow_process_intervals'];assert stats['dropped']==0
checks=0
for original,stored in zip(rows,stats['records']):
 for sample,retained in zip(original['child_stages']['sample_timings'],stored['sample_stages']):
  for stage in retained['slowest_assembly_stages']:
   phases=sample['assembly_stages'][stage['stage_index']].get('visibility_stages',[])
   expected=[[p['name'],p['count'],p['started_ns'],p['wall_ns'],p['thread_cycles']] for p in phases[:5]]
   assert stage['visibility_stages']==expected
   assert stage['visibility_stage_count']==len(phases)
   assert stage['visibility_stages_truncated']==(len(phases)>5)
   checks+=len(phases[:5])
assert checks>0
before=copy.deepcopy(stats);rows[0]['child_stages']['sample_timings'].clear();assert ledger.stats()['slow_process_intervals']==before
result=dict(result='PASS',requests=len(rows),visibility_phase_checks=checks,dropped=stats['dropped'],max_record_bytes=max(len(s.encode()) for s in ledger.slow),scope='Captured request retention parity and immutable bounded evidence; no live cadence claim.')
Path('work/camera/prototype-runs/slow-visibility-retention-20261009.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
