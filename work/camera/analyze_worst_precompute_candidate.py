import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
request=max(ledger['records'],key=lambda x:x['child_precompute_ns']);c=request['child_boundaries'];begin=c['constructed_ns'];end=c['sampled_ns'];assert end-begin==request['child_precompute_ns']
rows=[];last=begin;measured=0
for sample in request['sample_stages']:
 a=sample['started_ns'];b=sample['completed_ns'];assert last<=a<=b<=end and b-a==sample['wall_ns'];last=b;measured+=b-a
 for stage in sample['stages']:
  assert a<=stage['started_ns']<=stage['completed_ns']<=b
 for stage in sample['slowest_assembly_stages']:
  assert a<=stage['started_ns']<=stage['completed_ns']<=b and stage['thread_cycles']>=0
  rows.append(dict(alpha=sample['alpha'],name=stage['name'],wall_ms=stage['wall_ns']/1e6,thread_cycles=stage['thread_cycles']))
out=dict(result='PASS_WORST_PRECOMPUTE_PHASE_CONTAINMENT',older=request['older'],newer=request['newer'],precompute_ms=(end-begin)/1e6,measured_sample_ms=measured/1e6,between_sample_or_other_ms=(end-begin-measured)/1e6,retained_top_assembly_phases=sorted(rows,key=lambda x:x['wall_ms'],reverse=True),scope='All sample spans of worst retained slow request; assembly top3 per sample only. Thread cycles are raw counts, cannot convert to exclusive CPU time without qualification; no scheduler/driver cause proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
