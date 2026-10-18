"""Recorded boundary wall/CPU deltas; scheduling attribution remains indirect."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[];names=('native_pop','snapshot_lookup','exact_compare_or_copy','scene_match')
 for e in report['consumer_boundary_stage_samples']:
  cpu=e.get('thread_cpu_stamps')
  if cpu is None:continue
  wall=[e[k] for k in ('dequeued_ns','popped_ns','snapshot_ready_ns','copied_ns','matched_ns')]
  assert len(cpu)==5 and all(b>=a for a,b in zip(cpu,cpu[1:])) and all(b>=a for a,b in zip(wall,wall[1:]))
  for i,name in enumerate(names):
   rows.append(dict(refresh=e['refresh'],phase=name,wall_ms=(wall[i+1]-wall[i])/1e6,thread_cpu_ms=(cpu[i+1]-cpu[i])/1e6,frame_bytes=e['frame_bytes'],immutable_frame_reused=e.get('immutable_frame_reused',False)))
 assert rows,'Missing boundary CPU evidence'
 summary={name:{'samples':sum(r['phase']==name for r in rows),'max_wall_ms':max(r['wall_ms'] for r in rows if r['phase']==name),'max_thread_cpu_ms':max(r['thread_cpu_ms'] for r in rows if r['phase']==name)} for name in names}
 return dict(scope='Wall and per-thread CPU deltas over identical boundaries. CPU stamps may be quantized; wall-minus-CPU includes waiting/descheduling and does not exclusively prove GIL or lock contention.',phases=summary,worst_wall=sorted(rows,key=lambda r:r['wall_ms'],reverse=True)[:20],rows=rows)
if __name__=='__main__':
 p=Path(sys.argv[1]);r=analyze(json.loads(p.read_text()));p.with_suffix('.boundary-cpu.json').write_text(json.dumps(r,indent=2));print(json.dumps({'phases':r['phases'],'worst_wall':r['worst_wall'][:5]},indent=2))
