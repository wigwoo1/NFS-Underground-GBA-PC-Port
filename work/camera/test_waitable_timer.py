import time,json,statistics,threading
from pathlib import Path
from owned_waitable_timer import OwnedWaitableTimer
timer=OwnedWaitableTimer();rows={'sleep':[],'timer':[]}
try:
 for invalid in (0,-1,10000001):
  try:timer.wait_slice(invalid)
  except ValueError:pass
  else:raise AssertionError('invalid bounds accepted')
 errors=[]
 def foreign():
  try:timer.wait_slice(1000000)
  except AssertionError:errors.append('owner rejected')
 t=threading.Thread(target=foreign);t.start();t.join();assert errors==['owner rejected']
 for i in range(100):
  for name in (('sleep','timer') if i%2==0 else ('timer','sleep')):
   begin=time.perf_counter_ns()
   if name=='sleep':time.sleep(.001)
   else:timer.wait_slice(1000000)
   elapsed=time.perf_counter_ns()-begin;assert elapsed>0;rows[name].append(elapsed/1e6)
finally:timer.close();timer.close()
try:timer.wait_slice(1000000)
except RuntimeError:pass
else:raise AssertionError('closed timer accepted')
out=dict(result='PASS_OWNED_WAITABLE_TIMER',scope='Interleaved1ms component waits, no live cadence/game timing proof; short waits allow outer pause checks',metrics={k:dict(median_ms=statistics.median(v),max_ms=max(v)) for k,v in rows.items()},rows=rows)
Path('work/camera/waitable-timer-tests.json').write_text(json.dumps(out,indent=2));print(out['metrics'])
