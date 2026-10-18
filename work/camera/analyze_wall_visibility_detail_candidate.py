import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[];checks=0
for request in ledger['records']:
 for sample in request['sample_stages']:
  for stage in sample['slowest_assembly_stages']:
   encoded=stage.get('visibility_stages',[])
   phases=[dict(name=p[0],count=p[1],started_ns=p[2],completed_ns=p[2]+p[3],wall_ns=p[3],thread_cycles=p[4]) for p in encoded] if stage.get('visibility_stage_encoding')=='name_count_start_wall_cycles_v1' else encoded
   assert not stage.get('visibility_stages_truncated',False)
   assert len(phases)==stage.get('visibility_stage_count',0)
   for phase in phases:
    assert stage['started_ns']<=phase['started_ns']<=phase['completed_ns']<=stage['completed_ns']
    assert phase['wall_ns']==phase['completed_ns']-phase['started_ns'];checks+=1
   if phases:
    measured=sum(p['wall_ns'] for p in phases)
    assert measured<=stage['wall_ns']
    rows.append(dict(older=request['older'],newer=request['newer'],alpha=sample['alpha'],assembly_ms=stage['wall_ns']/1e6,unmeasured_ms=(stage['wall_ns']-measured)/1e6,phases=phases))
out=dict(result='PASS_BOUNDED_WALL_PHASE_CONTAINMENT',slow_requests=ledger['total'],phase_checks=checks,wall_samples=len(rows),largest=sorted(rows,key=lambda x:x['assembly_ms'],reverse=True)[:12],scope='Selected top3 assembly phases only; wall subphase coverage explicit. Elapsed time includes scheduling; not exclusive CPU or physical cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(result=out['result'],slow_requests=out['slow_requests'],phase_checks=checks,wall_samples=len(rows),largest=out['largest'][:2])))
