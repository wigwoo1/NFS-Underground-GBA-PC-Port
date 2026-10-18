"""Live preparation stage wall/cycle evidence; no exclusive cause attribution."""
import json,sys
from pathlib import Path
def analyze(report):
 jobs=[]
 for job in report['world_preparation_stage_samples']:
  if not job.get('sample_timings'):continue
  groups={};joins=[]
  for sample in job['sample_timings']:
   for stage in sample['assembly_stages']:
    assert stage['wall_ns']>=0 and stage['thread_cycles']>=0
    group=groups.setdefault(stage['name'],dict(wall_ns=0,cycles=0,calls=0))
    group['wall_ns']+=stage['wall_ns'];group['cycles']+=stage['thread_cycles'];group['calls']+=1
    if stage.get('frame_join_trace'):joins.append(stage['frame_join_trace'])
  jobs.append(dict(older=job['older'],newer=job['newer'],precompute_ms=job['precompute_ns']/1e6,precompute_cycles=job['precompute_thread_cycles'],construct_ms=job['construct_advance_ns']/1e6,stages={k:dict(wall_ms=v['wall_ns']/1e6,cycles=v['cycles'],calls=v['calls']) for k,v in groups.items()},joins=joins))
 return dict(result='PASS_STAGE_CYCLE_COVERAGE',jobs=len(jobs),largest=sorted(jobs,key=lambda j:j['precompute_ms'],reverse=True)[:12],scope='Inclusive stage wall time and thread execution cycles; CPU frequency, scheduling and GIL effects not isolated. Native join boundaries use raw QPC ticks/frequency.')
if __name__=='__main__':
 data=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(data,indent=2));print(json.dumps(dict(jobs=data['jobs'],largest=[{k:v for k,v in j.items() if k!='joins'} for j in data['largest'][:2]]),indent=2))
