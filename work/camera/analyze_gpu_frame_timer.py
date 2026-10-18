"""Correlate complete-frame GPU timestamps with CPU render intervals."""
import csv,json,statistics,sys
from pathlib import Path
prefix=Path(sys.argv[1]);gpu=list(csv.DictReader(Path(str(prefix)+'-gpu.csv').open()));cpu=list(csv.DictReader(Path(str(prefix)+'-components.csv').open()))
key=lambda r:(r['epoch'],r['target'],r['kind'])
assert gpu and len(gpu)==len(cpu)
assert len({key(r) for r in gpu})==len(gpu)
assert {key(r) for r in gpu}=={key(r) for r in cpu}
lookup={key(r):r for r in cpu};rows=[]
for r in gpu:
 begin,end,elapsed=(int(r[k]) for k in ('gpu_begin_ns','gpu_end_ns','gpu_elapsed_ns'))
 assert begin>0 and end>=begin and elapsed==end-begin
 c=lookup[key(r)];wall=(int(c['end_ns'])-int(c['begin_ns']))/1e6
 rows.append(dict(kind=int(r['kind']),gpu_ms=elapsed/1e6,cpu_wall_ms=wall,finish_wall_ms=float(c['finish_wall_ms'])))
def stats(values):
 v=sorted(values);return dict(count=len(v),sum_ms=sum(v),median_ms=statistics.median(v),p95_ms=v[int((len(v)-1)*.95)],max_ms=max(v))
report=dict(result='COMPLETE_GPU_TIMESTAMP_INTERVALS',prefix=str(prefix),gpu=stats([r['gpu_ms'] for r in rows]),cpu_wall=stats([r['cpu_wall_ms'] for r in rows]),finish_wall=stats([r['finish_wall_ms'] for r in rows]),scope='GPU timeline interval includes driver-command gaps and synchronization; not active utilization, scanout or 60-fps proof.')
budget=1000/60
report['budget_60hz_ms']=budget
report['over_budget']=dict(gpu=sum(r['gpu_ms']>budget for r in rows),cpu_wall=sum(r['cpu_wall_ms']>budget for r in rows),cpu_over_gpu_within=sum(r['cpu_wall_ms']>budget and r['gpu_ms']<=budget for r in rows),both=sum(r['cpu_wall_ms']>budget and r['gpu_ms']>budget for r in rows))
report['largest_gpu_frames']=sorted(rows,key=lambda r:r['gpu_ms'],reverse=True)[:5]
Path(str(prefix)+'-gpu-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
