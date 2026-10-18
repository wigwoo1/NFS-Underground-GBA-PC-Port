"""Compare preparation wall time with coarse Windows thread CPU evidence."""
import json,sys
from pathlib import Path
def analyze(report):
 rows=[]
 for x in report['world_preparation_stage_samples']:
  wall=x['construct_advance_ns']+x['precompute_ns'];cpu=x['construct_thread_cpu_ns']+x['precompute_thread_cpu_ns']
  assert wall>=0 and cpu>=0
  rows.append(dict(older=x['older'],newer=x['newer'],wall_ms=wall/1e6,coarse_thread_cpu_ms=cpu/1e6,construct_ms=x['construct_advance_ns']/1e6,precompute_ms=x['precompute_ns']/1e6,sample_count=len(x['sample_timings'])))
 assert rows
 long=[x for x in rows if x['wall_ms']>=100]
 return dict(scope='Windows thread CPU samples are quantized; individual CPU values may exceed short wall spans. Aggregates distinguish execution from elapsed time but cannot identify blocking, GIL, OS scheduling or driver causality.',jobs=len(rows),total_wall_ms=sum(x['wall_ms'] for x in rows),total_coarse_thread_cpu_ms=sum(x['coarse_thread_cpu_ms'] for x in rows),long_jobs=len(long),long_total_wall_ms=sum(x['wall_ms'] for x in long),long_total_coarse_thread_cpu_ms=sum(x['coarse_thread_cpu_ms'] for x in long),largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:12])
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.preparation-cpu-wall.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
