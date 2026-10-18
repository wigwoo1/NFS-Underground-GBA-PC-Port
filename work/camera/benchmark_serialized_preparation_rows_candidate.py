from pathlib import Path
import sys,json,time,statistics,gc
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_serialized_preparation_rows_candidate import PreparationRows
source=json.loads(Path('work/camera/prototype-runs/owned-native-1791588051903899800.json').read_text())['world_preparation_stage_samples']
assert gc.isenabled();rows=[]
for repeat in range(20):
 times={}
 for label in (('baseline','candidate') if repeat%2==0 else ('candidate','baseline')):
  target=[] if label=='baseline' else PreparationRows();begin=time.perf_counter_ns()
  for row in source:target.append(row)
  end=time.perf_counter_ns();times[label]=(end-begin)/1e6
  assert len(target)==len(source)
  if label=='candidate':assert target.snapshot()==source
  del target
 rows.append(times)
medians={k:statistics.median(x[k] for x in rows) for k in ('baseline','candidate')}
out=dict(result='PASS_EXACT_SERIALIZED_ROW_APPEND_BENCHMARK',requests=len(source),pairs=len(rows),medians_batch_ms=medians,added_mean_per_request_us=(medians['candidate']-medians['baseline'])*1000/len(source),rows=rows,normal_gc=gc.isenabled(),scope='Complete captured diagnostic batch append elapsed including scheduling; snapshot equality outside timed interval. Component only, no exclusive CPU or live attribution.')
Path('outputs/nfsug-native-renderer/camera-research/serialized-preparation-append-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print(out['medians_batch_ms'],out['added_mean_per_request_us'])
