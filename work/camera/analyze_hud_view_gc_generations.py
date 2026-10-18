import json,collections,statistics
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791412050703154400.json').read_text());rows=r['gc_collection_samples'];groups=[]
for generation in sorted({x['generation'] for x in rows}):
 for owner in sorted({x['thread_id'] for x in rows if x['generation']==generation}):
  selected=[x for x in rows if x['generation']==generation and x['thread_id']==owner];ms=[(x['end_ns']-x['start_ns'])/1e6 for x in selected]
  groups.append(dict(generation=generation,thread_id=owner,producer=owner==r['producer_thread_id'],count=len(selected),wall_total_ms=sum(ms),median_ms=statistics.median(ms),max_ms=max(ms),collected=sum(x['collected'] for x in selected),zero_collected=sum(x['collected']==0 for x in selected),uncollectable=sum(x['uncollectable'] for x in selected)))
longest=sorted(rows,key=lambda x:x['end_ns']-x['start_ns'],reverse=True)[:10]
for x in longest:
 x['wall_ms']=(x['end_ns']-x['start_ns'])/1e6
 x['preparation_overlaps']=[dict(older=p['older'],newer=p['newer'],overlap_ms=max(0,min(x['end_ns'],p['completed_ns'])-max(x['start_ns'],p['started_ns']))/1e6) for p in r['world_preparation_stage_samples'] if min(x['end_ns'],p['completed_ns'])>max(x['start_ns'],p['started_ns'])]
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-view-gc-generations-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='MEASURED',recorded_collections=len(rows),dropped=r['gc_trace_dropped'],groups=groups,longest=longest,scope='Recorded collector wall time/thread/generation with preparation timestamp overlaps; collected counts do not identify object types, memory leak or exclusive stall cause.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(groups))
