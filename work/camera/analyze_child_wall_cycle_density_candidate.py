"""Compare wall duration and execution cycles without converting cycle units."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
stages=[]
for request in ledger['records']:
 assert request['child_gc_dropped']==0
 for sample in request['sample_stages']:
  for stage in sample['stages']:
   if stage['wall_ns']<=0 or stage['thread_cycles']<=0:continue
   stages.append(dict(older=request['older'],newer=request['newer'],alpha=sample['alpha'],name=stage['name'],wall_ms=stage['wall_ns']/1e6,execution_cycles=stage['thread_cycles'],cycles_per_wall_ns=stage['thread_cycles']/stage['wall_ns']))
medians={name:statistics.median(s['cycles_per_wall_ns'] for s in stages if s['name']==name) for name in {s['name'] for s in stages}}
for s in stages:s['relative_cycle_density']=s['cycles_per_wall_ns']/medians[s['name']]
slow=sorted((s for s in stages if s['wall_ms']>=10),key=lambda s:s['wall_ms'],reverse=True)
out=dict(result='COMPLETE_RETAINED_CHILD_WALL_CYCLE_COMPARISON',requests=ledger['total'],stage_samples=len(stages),stage_median_cycles_per_wall_ns=medians,slow_stages=slow,scope='Complete retained slow-request ledger, not all requests. Execution cycles are never converted to elapsed CPU time. Low density may reflect scheduling, waiting or CPU frequency variation; not proof of exclusive off-CPU cause or algorithm cost.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print('requests',out['requests'],'slow',len(slow));print(slow[:5])
