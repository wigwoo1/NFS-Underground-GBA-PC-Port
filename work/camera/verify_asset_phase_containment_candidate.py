import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals']
assert ledger['dropped']==0 and len(ledger['records'])==ledger['total']
checks=0
for request in ledger['records']:
 for stage in request['construct_stages']:
  if 'asset_stages' not in stage:continue
  assert stage['asset_stage_encoding']=='name_start_wall_cycles_v1' and not stage['asset_stages_truncated']
  assert len(stage['asset_stages'])==stage['asset_stage_count']
  last=stage['started_ns'];total=0
  for name,start,wall,cycles in stage['asset_stages']:
   assert last<=start<=start+wall<=stage['completed_ns'] and wall>=0 and cycles>=0
   last=start+wall;total+=wall;checks+=1
  assert total<=stage['wall_ns']
assert checks>0
out=dict(result='PASS_COMPLETE_SLOW_ASSET_PHASES',requests=ledger['total'],phase_checks=checks,dropped=0,scope='All retained slow request asset phases, not complete per-sample assembly or visible cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
