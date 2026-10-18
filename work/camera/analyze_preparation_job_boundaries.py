"""Partition taken-job preparation latency with exact worker boundaries."""
import json,sys,statistics
from pathlib import Path
def analyze(report):
 jobs=report['preparation_queue_samples'];rows=[]
 for x in jobs:
  if x['status']!='taken' or x['identity'] is None:continue
  stamps=[x[k] for k in ('enqueued_ns','dequeued_ns','validated_ns','started_ns','finished_ns','published_ns','finalized_ns')]
  assert all(v is not None for v in stamps)
  assert all(b>=a for a,b in zip(stamps,stamps[1:]))
  phases=dict(zip(('queued_to_dequeue','validation','before_factory','factory','publication','finalization'),[(b-a)/1e6 for a,b in zip(stamps,stamps[1:])]))
  rows.append(dict(identity=x['identity'],generation=x['generation'],stages_ms=phases))
 assert rows
 return dict(scope='Worker wall-clock boundaries; queue includes preceding jobs; lock validation includes scheduling; no exclusive CPU attribution',jobs=len(rows),summary={k:dict(max_ms=max(x['stages_ms'][k] for x in rows),median_ms=statistics.median(x['stages_ms'][k] for x in rows)) for k in rows[0]['stages_ms']},largest_validation=sorted(rows,key=lambda x:x['stages_ms']['validation'],reverse=True)[:5],largest_finalization=sorted(rows,key=lambda x:x['stages_ms']['finalization'],reverse=True)[:5])
if __name__=='__main__':
 p=Path(sys.argv[1]);r=analyze(json.loads(p.read_text()));p.with_suffix('.job-boundaries.json').write_text(json.dumps(r,indent=2));print(json.dumps(r['summary'],indent=2))
