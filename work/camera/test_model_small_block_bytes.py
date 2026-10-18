import json,time,statistics,gc,sys
from pathlib import Path
from owned_motion_pairs import _decode_records
from owned_model_small_block_bytes_candidate import decode
folder=Path('work/camera/prototype-runs/child-scene-1791637661169682300');frames=[(folder/(x+'.frame.bin')).read_bytes() for x in ['older','newer']]
def signature(r):return (r['refresh'],r['epoch'],r['ticks'],[(x['kind'],x['context'],x['key'],tuple(bytes(b) for b in x['blocks'])) for x in r['records']])
reference=[signature(_decode_records(f,'models')) for f in frames];timings={False:[],True:[]};tracked={}
for iteration in range(40):
 for enabled in ((False,True) if iteration%2==0 else (True,False)):
  fn=decode if enabled else _decode_records;start=time.perf_counter_ns();results=[fn(f,'models') for f in frames];timings[enabled].append((time.perf_counter_ns()-start)/1e6)
  assert [signature(r) for r in results]==reference
  tracked[enabled]=sum(gc.is_tracked(b) for r in results for row in r['records'] for b in row['blocks'])
for f in frames:
 mutable=bytearray(f);result=decode(mutable,'models');assert all(isinstance(b,memoryview) for row in result['records'] for b in row['blocks'])
for f in [b'',frames[0][:39],b'BAD!'+frames[0][4:]]:
 errors=[]
 for fn in [_decode_records,decode]:
  try:fn(f,'models')
  except Exception as e:errors.append((type(e).__name__,str(e)))
  else:raise AssertionError('Malformed accepted')
 assert errors[0]==errors[1]
out=dict(result='PASS_SMALL_MODEL_BLOCK_PARITY',rounds=40,frames=160,baseline_ms=statistics.median(timings[False]),candidate_ms=statistics.median(timings[True]),tracked_blocks=tracked,scope='Two captured immutable endpoints/fullheader12blockmodelkey byteparity; mutableoriginalviewsemantics and3malformedcases preserved. Componentdecode timingonly, no fullsample/4K/livequalification; isolatednotinstalled.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/model-small-block-bytes-component.json').write_text(json.dumps(out,indent=2));print(out)
