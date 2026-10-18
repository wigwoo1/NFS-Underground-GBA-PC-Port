"""Verify committed frame precedes next draw within each source batch."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); groups={}
for x in r['presentation_samples']:
 if x.get('native_committed_sample'):groups.setdefault(x['batch_native_call_ns'],[]).append(x)
checks=0
for group in groups.values():
 rows=sorted(group,key=lambda x:x['batch_sample_position'])
 for a,b in zip(rows,rows[1:]):
  assert a['native_committed_sample'][6]<=b['sample_begin_ns'],(a['display_index'],b['display_index'])
  checks+=1
assert checks>0
out=Path(sys.argv[2]);out.write_text(json.dumps(dict(result='PASS',adjacent_checks=checks,batches=len(groups),scope='CPU commit before next draw within source batches; no scanout/cadence claim.'),indent=2));print('PASS',checks)
