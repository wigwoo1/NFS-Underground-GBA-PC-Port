import runpy,threading,time,statistics
from pathlib import Path
from owned_ordinary_model_visits import ordinary_model_visits,owned_object_chains,_chain_local
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');old={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/ordinary-chain-cache-20261006/before.py').read_text(),old)
portal=v['prepared'].pair.portal
for i in range(101):
 queue=portal.sample(i/100)
 for scene in v['scenes']:
  for inactive in (False,True):assert old['ordinary_model_visits'](scene.graph,queue,inactive)==ordinary_model_visits(scene.graph,queue,inactive)
closed=v['scenes'][0].graph;cached=owned_object_chains(closed);assert owned_object_chains(closed) is cached
other=[]
t=threading.Thread(target=lambda:other.append(owned_object_chains(closed)));t.start();t.join();assert other[0]==cached and other[0] is not cached
try:cached[0]=()
except TypeError:pass
else:raise AssertionError('mutable chains')
times=[[],[]];queue=portal.sample(0)
for repeat in range(10):
 for index in ((0,1) if repeat%2==0 else (1,0)):
  begin=time.perf_counter_ns()
  for j in range(50):(old['ordinary_model_visits'],ordinary_model_visits)[index](closed,queue)
  times[index].append((time.perf_counter_ns()-begin)/1e6)
assert len(_chain_local.cache)<=4
print('PASS404 exact visits, immutable bounded chains/thread isolation; median50calls ms',*[statistics.median(x) for x in times])
