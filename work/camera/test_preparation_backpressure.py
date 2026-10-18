"""Capacity stays bounded while producers wait, and cancellation is prompt."""
import threading,time
from owned_preparation_pipeline import PreparationPipeline
class Owned:
 def __init__(self):self.closed=False
 def close(self):self.closed=True
p=PreparationPipeline(1);first=p.submit(Owned);first.result(5);submitted=threading.Event();started=threading.Event();result=[]
def producer():
 started.set();result.append(p.submit(Owned,timeout=5));submitted.set()
t=threading.Thread(target=producer);t.start();assert started.wait(5)
assert not submitted.wait(.05),'Capacity increased while an owned result remains retained'
value=p.take(first);value.close();assert submitted.wait(5);t.join(5);second=p.take(result[0]);second.close()
held=p.submit(Owned);held.result(5)
try:p.submit(Owned,timeout=.05)
except RuntimeError as e:assert str(e)=='Preparation queue stalled'
else:raise AssertionError('Wait timeout ignored')
cancel=threading.Event();errors=[];started.clear()
def cancellable():
 started.set()
 try:p.submit(Owned,timeout=5,abort=cancel.is_set)
 except RuntimeError as e:errors.append(str(e))
t=threading.Thread(target=cancellable);t.start();assert started.wait(5);cancel.set();t.join(1);assert not t.is_alive() and errors==['Preparation submission cancelled']
value=p.take(held);value.close();p.close()
print('PASS bounded producer wait, capacity release, timeout and cancellation')
