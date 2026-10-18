from pathlib import Path
import sys,types,time,statistics,json
sys.path.insert(0,str(Path('work/camera').resolve()))
env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
import owned_complete_road_gpu as road
from owned_road_encode_flat_join_candidate import encode_road as candidate
fn=road.encode_road;original=types.FunctionType(fn.__code__,fn.__globals__,fn.__name__,fn.__defaults__,fn.__closure__);calls=[]
def record(context,candidate,bounds):
 _road_calls.append((context,candidate,bounds));return _road_original(context,candidate,bounds)
fn.__globals__.update(_road_calls=calls,_road_original=original);fn.__code__=record.__code__
try:
 history,prepared=env['prepare']();samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas']);samples.close();history.close()
finally:fn.__code__=original.__code__
assert calls
for args in calls:assert candidate(*args)==original(*args)
rows=[]
for i in range(40):
 row={}
 for label in (('baseline','candidate') if i%2==0 else ('candidate','baseline')):
  begin=time.perf_counter_ns()
  for args in calls:(original if label=='baseline' else candidate)(*args)
  row[label]=(time.perf_counter_ns()-begin)/1e6
 rows.append(row)
fn.__code__=candidate.__code__
try:
 history,prepared=env['prepare']();packets=[]
 try:samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas'],on_sample=packets.append);samples.close();assert [env['fingerprint'](p) for p in packets]==env['expected']
 finally:history.close()
finally:fn.__code__=original.__code__
out=dict(result='PASS_ROAD_FLAT_JOIN_EXACT_COMPONENT',records=len(calls),six_sample_parity=True,medians_ms={k:statistics.median(x[k] for x in rows) for k in ('baseline','candidate')},scope='One saved fixture, 40 alternating full record batches, validation unchanged; no live or native4K claim.')
Path('outputs/nfsug-native-renderer/camera-research/road-flat-join-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)
