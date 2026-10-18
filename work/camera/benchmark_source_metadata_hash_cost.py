"""Measure identity hashing without changing production identity validation."""
import json,time,statistics
from pathlib import Path
from owned_motion_pairs import _decode_records
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={}
exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];frames=[v[0] for v in owner.samples.values()];owner.close();ns['history'].close()
try:
 sizes=[]
 for frame in frames:
  full=_decode_records(frame);plain=_decode_records(frame,False)
  assert (full['epoch'],full['refresh'],full['ticks'])==(plain['epoch'],plain['refresh'],plain['ticks'])
  assert len(full['records'])==len(plain['records'])
  for a,b in zip(full['records'],plain['records']):
   assert a['kind']==b['kind'] and a['context']==b['context'] and a['blocks']==b['blocks'] and b['key'] is None
  sizes.append(dict(frame_bytes=len(frame),records=len(full['records']),identity_bytes=sum(sum(len(r['blocks'][i]) for i in ((0,1,2,9) if r['kind']==1 else (0,1,7) if r['kind']==2 else (1,4,5,6,7,8))) for r in full['records'])))
 timings={True:[],False:[]}
 for trial in range(20):
  for enabled in ((True,False) if trial%2==0 else (False,True)):
   start=time.perf_counter_ns()
   for frame in frames:_decode_records(frame,enabled)
   timings[enabled].append((time.perf_counter_ns()-start)/1e6)
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-metadata-hash-cost-20261007');cp.mkdir(exist_ok=True)
 result=dict(result='MEASURED',samples=sizes,median_eight_decodes_ms={str(k):statistics.median(v) for k,v in timings.items()},trials_ms={str(k):v for k,v in timings.items()},scope='Alternating uncached actual scene decodes. Disabling keys diagnostic only; production identity checks unchanged. Not live cadence or exclusive cause proof.')
 (cp/'result.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(result['median_eight_decodes_ms'],sizes)
finally:frames.clear()