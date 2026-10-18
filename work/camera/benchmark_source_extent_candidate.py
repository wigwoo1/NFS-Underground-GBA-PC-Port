"""Alternating validation comparison on actual captured source endpoints."""
import json,time,tracemalloc,statistics,gc
from pathlib import Path
from owned_motion_pairs import _decode_records
from owned_source_extent_decode_candidate import extents
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791539869506441500.json').read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'captured-extent-benchmark','exec'),ns);ns['prepared'].close();ns['history'].close();frames=ns['frames']
def original(frame):
 s=_decode_records(frame,source_keys=False)
 return s['epoch'],s['refresh'],[len(r['blocks'][5]) if r['kind']==3 else 0 for r in s['records']]
for f in frames:assert original(f)==extents(f)
rows=[]
for i in range(80):
 for name,fn in ([('original',original),('extent',extents)] if i%2==0 else [('extent',extents),('original',original)]):
  start=time.perf_counter_ns()
  for f in frames:fn(f)
  rows.append(dict(iteration=i,variant=name,wall_ns=time.perf_counter_ns()-start))
allocation={}
for name,fn in [('original',original),('extent',extents)]:
 gc.collect();tracemalloc.start();before=tracemalloc.get_traced_memory()[0]
 for f in frames:fn(f)
 current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();allocation[name]=dict(current_delta=current-before,peak_delta=peak-before)
out=dict(result='PASS_CAPTURED_SOURCE_EXTENT_PARITY',source_records=[len(extents(f)[2]) for f in frames],median_ms={name:statistics.median(r['wall_ns']/1e6 for r in rows if r['variant']==name) for name in ('original','extent')},allocation=allocation,rows=rows,scope='80 alternating two-endpoint captured validation pairs; allocation tracing separate from timing. Does not establish live cadence gain or collected-object origin.')
Path('work/camera/prototype-runs/source-extent-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
