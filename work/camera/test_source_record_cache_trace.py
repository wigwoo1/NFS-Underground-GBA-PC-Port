import runpy,json
from pathlib import Path
import owned_motion_pairs as candidate
baseline=runpy.run_path('work/camera/owned_motion_pairs.py.before-record-trace')
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];frames=[v[0] for v in owner.samples.values()];owner.close();ns['history'].close();candidate._record_cache.entries=[];traces=[]
for frame in frames:
 for mutable in (False,True):
  value=bytearray(frame) if mutable else frame;t=[]
  a=baseline['records'](value);b=candidate.records(value,t)
  assert a==b
  traces.append(t)
  b['records'][0]['blocks'].clear();b['records'][0]['key']=None
  assert candidate.records(value)==baseline['records'](value)
 hit_trace=[];assert candidate.records(frame,hit_trace)==baseline['records'](frame);traces.append(hit_trace)
 assert len(candidate._record_cache.entries)<=4
assert any(any(x['name']=='uncached_decode' for x in t) for t in traces)
assert any(any(x['name']=='cache_lookup' and x['hit'] for x in t) for t in traces)
for frame in (b'',frames[0][:-1],b'BAD!'+frames[0][4:]):
 for decoder in (baseline['records'],candidate.records):
  try:decoder(frame)
  except ValueError:pass
  else:raise AssertionError('Malformed frame accepted')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-record-cache-trace-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',frames=len(frames),mutable_and_immutable_cases=len(frames)*2,cache_bounded=True,caller_container_independent=True,malformed_cases=3,traces=traces,scope='Actual captured frame metadata exact baseline, trace scope and cache ownership; no live performance proof'),indent=2))
for name in ('test_source_record_cache_trace.py','owned_motion_pairs.py','owned_motion_pairs.py.before-record-trace','owned_source_model_anchor_candidate.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print('PASS 16 mutable/immutable metadata cases, cache hits/misses, private containers and malformed frames')