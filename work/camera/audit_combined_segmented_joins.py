import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());joins=[]
def visit(v):
 if isinstance(v,dict):
  if v.get('name')=='immutable_frame_join':joins.append(v)
  for x in v.values():visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
visit(r['world_preparation_stage_samples'])
assert joins
for j in joins:
 t=j['frame_join_trace'];assert t['segmented'] and not t['materialized'];assert t['retained_tail_bytes']>0
out=dict(result='PASS_LIVE_SEGMENTED_JOINS',joins=len(joins),retained_tail_bytes_min=min(j['frame_join_trace']['retained_tail_bytes'] for j in joins),median_join_ms=statistics.median((j['completed_ns']-j['started_ns'])/1e6 for j in joins),scope='Recorded live preparation joins retain tails without materialization. Does not certify later presentation ownership or physical cadence.')
a=json.loads(Path('work/camera/combined-segmented-gpu.json').read_text());b=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-source-gpu-20261007/original-gpu-parity.json').read_text());assert a['checks']==b['checks']
out['archive_4k_checks_exact']=True
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
