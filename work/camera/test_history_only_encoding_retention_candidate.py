import json,copy
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791557740164926100.json').read_text());row=copy.deepcopy(r['world_preparation_stage_samples'][0]);child=row['child_stages'];child['encoding_cleanup']=None;child['source_sidecar_trace']=None;child['encode_samples']=[];child['history_only']=True
ledger=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1);ledger.append(row);stats=ledger.stats()['slow_process_intervals'];assert stats['total']==1 and stats['dropped']==0
stored=stats['records'][0];assert stored['encoding_cleanup']=={} and stored['source_sidecar_trace']=={} and stored['encode_samples']==[]
out=dict(result='PASS_OPTIONAL_HISTORY_ONLY_ENCODING_RETENTION',scope='Explicit absent encoding/cleanup telemetry accepted; source preparation semantics unchanged, live rerun required.')
Path('work/camera/prototype-runs/history-only-encoding-retention-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
