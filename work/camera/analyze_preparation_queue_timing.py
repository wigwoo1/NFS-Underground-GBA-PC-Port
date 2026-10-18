"""Audit bounded preparation job lifecycle and separate queue stage wall times."""
import json,sys,statistics
from pathlib import Path

def analyze(r):
 rows=[]
 for t in r['preparation_queue_samples']:
  if t['status']!='taken' or t['identity'] is None:continue
  stamps=[t[k] for k in ('submitted_ns','enqueued_ns','started_ns','finished_ns','published_ns','taken_ns')]
  assert all(y>=x for x,y in zip(stamps,stamps[1:]));assert len(t['identity'])==3
  phases=dict(zip(('capacity_admission_ms','queued_before_start_ms','factory_ms','publication_ms','ready_before_take_ms'),[(y-x)/1e6 for x,y in zip(stamps,stamps[1:])]))
  rows.append(dict(identity=t['identity'],generation=t['generation'],**phases))
 assert rows
 keys=('capacity_admission_ms','queued_before_start_ms','factory_ms','publication_ms','ready_before_take_ms')
 return dict(scope='Exact wall boundaries by epoch/source pair/generation. Queue time includes preceding work and scheduling; ready-before-take includes intentional buffering, not necessarily a stall.',jobs=len(rows),summary={k:dict(median_ms=statistics.median(x[k] for x in rows),max_ms=max(x[k] for x in rows),over_100ms=sum(x[k]>100 for x in rows)) for k in keys},largest_queue_waits=sorted(rows,key=lambda x:x['queued_before_start_ms'],reverse=True)[:12],lifecycle_counts={s:sum(t['status']==s for t in r['preparation_queue_samples']) for s in sorted({t['status'] for t in r['preparation_queue_samples']})})
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.queue-timing.json').write_text(json.dumps(a,indent=2));print(json.dumps(a['summary'],indent=2))
