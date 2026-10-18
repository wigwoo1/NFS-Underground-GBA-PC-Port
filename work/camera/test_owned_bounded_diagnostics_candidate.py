import json
from pathlib import Path
from owned_bounded_diagnostics_candidate import BoundedPresentationDiagnostics
r=BoundedPresentationDiagnostics(3,200)
for i in range(10000):
 r.append(dict(index=i));r[-1]['pause']=i%2==0
 assert len(r)<=3 and r.bytes<=200
assert [x['index'] for x in r]==[9997,9998,9999]
assert [x['index'] for x in reversed(r)]==[9999,9998,9997]
assert r.total_records==10000 and r.dropped_records==9997
small=BoundedPresentationDiagnostics(100,60)
for i in range(30):small.append(dict(index=i,text='abcdefgh'));assert small.bytes+len(json.dumps(small.tail,separators=(',',':')).encode())<=60
before=small.snapshot()
try:small.append(dict(text='x'*100))
except ValueError:pass
else:raise AssertionError('Oversized record accepted')
assert small.snapshot()==before
out=dict(result='PASS_BOUNDED_DIAGNOSTIC_WINDOW',record_limit=r.stats(),byte_limit=small.stats(),scope='Component retention/latest-metadata checks only; no live timing claim.')
Path('work/camera/prototype-runs/native-bounded-diagnostics-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
