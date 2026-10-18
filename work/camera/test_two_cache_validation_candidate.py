import json,struct,sys
from pathlib import Path
import owned_motion_pairs as m
from owned_record_cache_two_candidate import records as candidate
frame=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes()
cases=[('empty',b''),('short',frame[:39])]
for offset in [0,24,32,40,44,52,56]:
 b=bytearray(frame);struct.pack_into('<I',b,offset,0xffffffff);cases.append((str(offset),bytes(b)))
results=[]
for name,value in cases:
 outcomes=[]
 for fn in (m.records,candidate):
  m._record_cache.entries=[]
  try:fn(value);outcomes.append(('accepted',''))
  except Exception as e:outcomes.append((type(e).__name__,str(e)))
 assert outcomes[0]==outcomes[1]
 results.append(dict(mutation=name,error=outcomes[0]))
frames=[bytes(bytearray(frame)) for _ in range(6)]
for fn in (m.records,candidate):
 m._record_cache.entries=[]
 for f in frames:assert fn(f)==m._decode_records(f)
 for f in frames:assert fn(f)==m._decode_records(f)
 if fn is candidate:assert len(m._record_cache.entries)==2
m._record_cache.entries=[]
assert sum(x['error'][0]!='accepted' for x in results)>=7
out=dict(result='PASS_FIXED_WIDTH_MUTATION_AND_CACHE_REVISIT_PARITY',cases=results,revisit_checks=24)
Path('work/camera/prototype-runs/two-cache-fixed-validation-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
