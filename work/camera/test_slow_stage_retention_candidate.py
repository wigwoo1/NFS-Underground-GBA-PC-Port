import json,sys
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path(sys.argv[1]).read_text());source=r['world_preparation_stage_samples'];owner=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=4096)
for row in source:owner.append(row)
report=owner.stats()['slow_process_intervals'];assert report['dropped']==0 and report['total']==len(source)
for original,retained in zip(source,report['records']):
 assert not retained['stage_records_truncated']
 assert [(x['name'],x['wall_ns']) for x in retained['construct_stages']]==[(x['name'],x['wall_ns']) for x in original['child_stages']['construct_stages']]
 assert len(retained['sample_stages'])==len(original['child_stages']['sample_timings'])
assert len(owner.snapshot())==2
# Serialized ownership does not retain caller structures after publication.
expected=json.dumps(report,sort_keys=True);source[0]['child_stages']['construct_stages'].clear();assert json.dumps(owner.stats()['slow_process_intervals'],sort_keys=True)==expected
out=dict(result='PASS_BOUNDED_SCALAR_STAGE_RETENTION',requests=report['total'],recent_window=2,stage_records_truncated=0,scope='Captured scalar stage equality survives recent-window eviction and caller mutation; bounded serialized ledger, not live performance proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
