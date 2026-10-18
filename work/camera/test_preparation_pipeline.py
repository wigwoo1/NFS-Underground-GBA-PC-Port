import threading
from concurrent.futures import CancelledError
from owned_preparation_pipeline import PreparationPipeline
class Owned:
 def __init__(self):self.closed=0
 def close(self):self.closed+=1
pipeline=PreparationPipeline(1);started=threading.Event();release=threading.Event();old=Owned()
def factory():started.set();release.wait(5);return old
future=pipeline.submit(factory);assert started.wait(5)
try:pipeline.submit(Owned)
except ValueError:pass
else:raise AssertionError('Unbounded preparation accepted')
pipeline.invalidate();release.set();pipeline.thread.join(.05)
# Wait for the worker to process a following notification, without timing guesses.
new_future=None
for _ in range(100):
 try:new_future=pipeline.submit(Owned);break
 except ValueError:threading.Event().wait(.01)
assert new_future is not None
new=pipeline.take(new_future);assert future.cancelled() and old.closed==1 and new.closed==0
new.close();pipeline.close();pipeline.close();assert not pipeline.thread.is_alive()
print('PASS bounded preparation, stale generation cleanup, explicit ownership transfer and idempotent shutdown')

pipeline=PreparationPipeline(1)
def fail():raise ValueError('owned preparation failure')
f=pipeline.submit(fail)
try:pipeline.take(f)
except ValueError as error:assert str(error)=='owned preparation failure'
else:raise AssertionError('Preparation failure lost')
f=pipeline.submit(Owned);value=f.result(5);pipeline.invalidate()
assert value.closed==1
try:pipeline.take(f)
except CancelledError:pass
else:raise AssertionError('Invalidated ownership transferred')
pipeline.close();assert value.closed==1
print('PASS preparation failure frees capacity and ready invalidation prevents stale transfer')
