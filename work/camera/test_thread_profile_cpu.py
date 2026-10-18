import sys,time,json,tempfile,threading
from pathlib import Path
from owned_thread_profile import ThreadProfile
def waiting():time.sleep(.06)
def working():
 end=time.thread_time_ns()+62500000
 value=0
 while time.thread_time_ns()<end:value+=1
 return value
def failing():raise RuntimeError('expected')
profile=ThreadProfile();previous=sys.getprofile()
profile.run(waiting);profile.run(working)
assert sys.getprofile() is previous and not profile.active
try:profile.run(failing)
except RuntimeError:pass
else:raise AssertionError('exception swallowed')
assert sys.getprofile() is previous and not profile.active
profile.owner=-1;profile.event(sys._getframe(),'call',None);assert profile.foreign_events==1
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'profile.json';profile.save(p);r=json.loads(p.read_text());rows={x['function']:x for x in r['rows']}
 for name in ('waiting','working','failing'):
  x=rows[name];assert x['calls']==1 and x['inclusive_wall_ns']>=0 and x['inclusive_thread_cpu_ns']>=0
  assert x['wall_minus_coarse_cpu_ns']==x['inclusive_wall_ns']-x['inclusive_thread_cpu_ns']
 assert rows['waiting']['inclusive_wall_ns']>40000000
 assert rows['working']['inclusive_thread_cpu_ns']>=62500000
 print(json.dumps(dict(result='PASS',waiting=rows['waiting'],working=rows['working'],scope='CPU measurement, wait/work separation, exceptions, profiler restoration, foreign events and JSON schema')))
