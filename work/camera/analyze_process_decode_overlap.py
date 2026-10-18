"""Correlate measured parent decode phases with producer activity, without causal claims."""
import json,sys,statistics
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text())
def overlap_union(start,end,rows):
 spans=sorted((max(start,r['started_ns']),min(end,r['completed_ns'])) for r in rows if r['started_ns']<end and r['completed_ns']>start)
 total=0;right=start
 for a,b in spans:
  if b>max(a,right):total+=b-max(a,right)
  right=max(right,b)
 assert 0<=total<=end-start
 return total
stages=[]
for job in d['world_preparation_stage_samples']:
 for s in job.get('parent_decode_stages',[]):
  assert s['completed_ns']-s['started_ns']==s['wall_ns'] and s['thread_cycles']>=0
  start,end=s['started_ns'],s['completed_ns']
  stages.append(dict(older=job['older'],newer=job['newer'],**s,original_update_overlap_ns=overlap_union(start,end,d['original_update_samples']),source_capture_overlap_ns=overlap_union(start,end,d['producer_cycle_samples'])))
joins=[s for s in stages if s['name']=='frame_join']
result=dict(scope='Same host-clock intervals; overlap is concurrency evidence, not exclusive CPU/GIL or scheduling cause. Raw thread cycles have no frequency conversion.',checked_phases=len(stages),frame_joins=len(joins),median_join_ms=statistics.median(s['wall_ns'] for s in joins)/1e6,median_join_cycles=statistics.median(s['thread_cycles'] for s in joins),joins_over_refresh=sum(s['wall_ns']>1e9/60 for s in joins),longest=sorted(joins,key=lambda s:s['wall_ns'],reverse=True)[:12])
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
