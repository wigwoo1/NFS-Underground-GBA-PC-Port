from concurrent.futures import CancelledError
from owned_preparation_pipeline import PreparationPipeline
from pathlib import Path
import json
class Owned:
 def __init__(self):self.closed=0
 def close(self):self.closed+=1
checks=[]
p=PreparationPipeline(1)
try:
 first=Owned();f=p.submit(lambda:first);assert f.result(2) is first
 original=f.result
 def retire_after_result(timeout=None):
  result=original(timeout);p.invalidate();return result
 f.result=retire_after_result
 try:p.take(f,2)
 except CancelledError:pass
 else:raise AssertionError('Retired result must be cancelled')
 assert first.closed==1;checks.append('invalidate between ready result and ownership claim')
 second=Owned();g=p.submit(lambda:second);assert p.take(g,2) is second
 try:p.take(g,2)
 except ValueError:pass
 else:raise AssertionError('Duplicate take must still fail')
 second.close();checks.append('capacity reclaimed and duplicate take rejected')
 third=Owned();h=p.submit(lambda:third);assert h.result(2) is third;p.invalidate()
 try:p.take(h,2)
 except CancelledError:pass
 else:raise AssertionError('Already retired result must be cancelled')
 assert third.closed==1;checks.append('already-ready invalidation closes exactly once')
finally:p.close()
assert not p.thread.is_alive();checks.append('clean shutdown')
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-preparation-pause-race-20261006');(out/'tests.json').write_text(json.dumps(checks,indent=2));print('PASS',checks)
