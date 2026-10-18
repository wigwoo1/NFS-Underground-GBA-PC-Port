import json,copy
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791552464295452400.json').read_text());rows=r['world_preparation_stage_samples'];retention=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=4096)
for row in rows:retention.append(row)
stats=retention.stats()['slow_process_intervals'];assert stats['dropped']==0 and len(stats['records'])==len(rows)
checks=0
for original,stored in zip(rows,stats['records']):
 for sample,retained in zip(original['child_stages']['sample_timings'],stored['sample_stages']):
  expected=sorted(enumerate(sample.get('assembly_stages',[])),key=lambda item:item[1]['wall_ns'],reverse=True)[:3]
  assert retained['assembly_stage_count']==len(sample.get('assembly_stages',[]))
  assert [(s['stage_index'],s['name'],s['wall_ns']) for s in retained['slowest_assembly_stages']]==[(i,s['name'],s['wall_ns']) for i,s in expected];checks+=len(expected)
before=copy.deepcopy(stats);rows[0]['child_stages']['sample_timings'].clear();assert retention.stats()['slow_process_intervals']==before
out=dict(result='PASS_BOUNDED_SLOW_ASSEMBLY_RETENTION',requests=len(rows),stage_checks=checks,recent_capacity=2,slow_records=len(stats['records']),dropped=stats['dropped'],scope='Retains top3 assembly phases per sample by elapsed time; explicit total phase count. Not complete substage coverage or causal attribution.')
Path('work/camera/prototype-runs/slow-assembly-retention-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
