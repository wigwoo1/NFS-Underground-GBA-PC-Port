import threading,time,sys
from owned_thread_profile import ThreadProfile
ready=threading.Event();done=threading.Event();results={}
def producer_marker():return sum(range(200))
def preparation_marker():return sum(range(300))
def work():
 ready.set()
 while not done.is_set():preparation_marker();time.sleep(.001)
def worker():
 p=ThreadProfile();previous=sys.getprofile();p.run(work);assert sys.getprofile() is previous;results['profile']=p
thread=threading.Thread(target=worker);thread.start();assert ready.wait(5)
for i in range(500):producer_marker();time.sleep(.0001)
done.set();thread.join(5);assert not thread.is_alive()
p=results['profile'];names={key[2] for key in p.rows};assert 'preparation_marker' in names and 'producer_marker' not in names
assert not p.active
q=ThreadProfile()
def fail():raise ValueError('expected')
previous=sys.getprofile()
try:q.run(fail)
except ValueError:pass
else:raise AssertionError('exception suppressed')
assert sys.getprofile() is previous and not q.active
print('PASS producer excluded, owner functions captured, previous profile restored on success/failure')
