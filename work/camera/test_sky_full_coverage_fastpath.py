import json,time,statistics
from pathlib import Path
setup=Path('work/camera/test_owned_sky_frame.py').read_text().split("\ncp=Path")[0];ns={};exec(compile(setup,'sky-fixture','exec'),ns)
from owned_sky_frame import attach_sky
scene=ns['scene'];frame=ns['result'];offset=ns['offset']
source=Path('work/camera/owned_sky_frame.py').read_text();start=source.index(' if coverage.count(0)!=len(coverage):');end=source.index(' # One owned output allocation',start)
original=source[:start]+" if coverage.count(0)!=len(coverage):\n  for i in range(10560,25696):\n   if frame[offset+38400+i] not in (0,1):raise ValueError('Invalid sky coverage')\n   if frame[offset+38400+i] and frame[offset+i]!=indices[i-10560]:raise ValueError('Conflicting original sky ownership')\n"+source[end:];old={};exec(compile(original,'old-sky-check','exec'),old)
cases=[('covered',frame)]
for label in ('mixed','conflict','invalid','uncovered'):
 b=bytearray(frame)
 if label=='mixed':b[offset+38400+10560]=0
 elif label=='conflict':b[offset+10560]^=1
 elif label=='invalid':b[offset+38400+10560]=2
 else:b[offset+38400+10560:offset+38400+25696]=bytes(15136)
 cases.append((label,bytes(b)))
checks=[]
for label,payload in cases:
 for value in (payload,bytearray(payload),memoryview(payload)):
  outcomes=[]
  for fn in (old['attach_sky'],attach_sky):
   try:outcomes.append(('ok',fn(value,scene)))
   except ValueError as exc:outcomes.append(('error',str(exc)))
  assert outcomes[0]==outcomes[1];checks.append(label)
times={'reference':[],'bulk':[]}
for i in range(30):
 order=[('reference',old['attach_sky']),('bulk',attach_sky)]
 if i%2:order.reverse()
 for name,fn in order:
  begin=time.perf_counter_ns();fn(frame,scene);times[name].append(time.perf_counter_ns()-begin)
out=dict(exact_cases=len(checks),medians_ns={k:statistics.median(v) for k,v in times.items()},scope='Actual owned sky/captured frame, coverage/error/input-type parity; fixed covered endpoint component timing only')
Path('work/camera/prototype-runs/sky-full-coverage-fastpath.json').write_text(json.dumps(out,indent=2));print('PASS',out)
