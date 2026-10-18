"""Exact same-host interval overlap; no exclusive causal attribution."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[];checks=0
for request in ledger['records']:
 assert request['child_gc_dropped']==0
 gc=request['child_gc_rows']
 for sample in request['sample_stages']:
  for stage in sample['slowest_assembly_stages']:
   if stage['name']!='main_graph_surfaces':continue
   encoded=stage.get('visibility_stages',[])
   phases=[dict(name=p[0],started_ns=p[2],completed_ns=p[2]+p[3],wall_ns=p[3],thread_cycles=p[4]) for p in encoded] if stage.get('visibility_stage_encoding')=='name_count_start_wall_cycles_v1' else encoded
   for phase in phases:
    overlap=sum(max(0,min(phase['completed_ns'],g['end_ns'])-max(phase['started_ns'],g['start_ns'])) for g in gc)
    assert 0<=overlap<=phase['wall_ns'];checks+=1
    if phase['wall_ns']>5000000:rows.append(dict(older=request['older'],newer=request['newer'],alpha=sample['alpha'],phase=phase['name'],elapsed_ms=phase['wall_ns']/1e6,gc_overlap_ms=overlap/1e6,elapsed_outside_gc_ms=(phase['wall_ns']-overlap)/1e6,thread_cycles=phase['thread_cycles']))
out=dict(result='PASS_WALL_GC_OVERLAP',slow_requests=ledger['total'],phase_checks=checks,over_5ms=len(rows),largest=sorted(rows,key=lambda x:x['elapsed_ms'],reverse=True)[:20],scope='Selected top3 assembly phases, complete retained GC rows and exact interval intersections. Elapsed outside GC includes scheduling/native waits; not exclusive CPU or gameplay cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
