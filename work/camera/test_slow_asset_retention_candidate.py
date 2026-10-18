import json,copy
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791555631470042000.json').read_text());rows=r['world_preparation_stage_samples']
ledger=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=4096)
for row in rows:ledger.append(row)
stats=ledger.stats()['slow_process_intervals'];assert stats['dropped']==0
checks=0
for original,stored in zip(rows,stats['records']):
 for phase,retained in zip(original['child_stages']['construct_stages'],stored['construct_stages']):
  assets=phase.get('asset_stages',[])
  if assets:
   assert retained['asset_stages']==[[p['name'],p['started_ns'],p['wall_ns'],p['thread_cycles']] for p in assets[:5]]
   assert retained['asset_stage_count']==len(assets) and retained['asset_stages_truncated']==(len(assets)>5)
   checks+=len(assets)
assert checks>0
before=copy.deepcopy(stats);rows[0]['child_stages']['construct_stages'].clear();assert ledger.stats()['slow_process_intervals']==before
out=dict(result='PASS_CAPTURED_ASSET_RETENTION',requests=len(rows),phase_checks=checks,dropped=stats['dropped'],max_record_bytes=max(len(s.encode()) for s in ledger.slow),scope='Captured retention parity and caller isolation, not cadence proof.')
Path('work/camera/prototype-runs/slow-asset-retention-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
