"""Compare raw thread execution cycles and host elapsed preparation time."""
import json,sys,statistics
from pathlib import Path

def analyze(report):
 rows=[]
 for x in report['world_preparation_stage_samples']:
  assert x['started_ns']<=x['constructed_ns']<=x['completed_ns']
  a=x['construct_thread_cycles'];b=x['precompute_thread_cycles'];assert a>=0 and b>=0
  rows.append(dict(older=x['older'],newer=x['newer'],wall_ms=(x['completed_ns']-x['started_ns'])/1e6,construct_cycles=a,precompute_cycles=b,total_cycles=a+b))
 assert rows
 return dict(scope='Raw current-thread execution cycles versus host elapsed wall time; cycles are not nanoseconds, frequency is not assumed, and this cannot identify GIL, OS or driver as a specific cause.',jobs=len(rows),median_wall_ms=statistics.median(x['wall_ms'] for x in rows),median_cycles=statistics.median(x['total_cycles'] for x in rows),longest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:15])
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.preparation-cycles.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
