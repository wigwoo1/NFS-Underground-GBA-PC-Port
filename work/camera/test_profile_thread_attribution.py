"""Runtime control for cProfile cross-thread attribution; diagnostic only."""
import cProfile,pstats,threading,time,json,sys
from pathlib import Path
ready=threading.Event();done=threading.Event();result={}
def producer_marker():return sum(range(200))
def preparation_marker():return sum(range(300))
def profiled_work():
 ready.set()
 while not done.is_set():preparation_marker();time.sleep(.001)
def worker():
 result['worker_thread']=threading.get_ident();profile=cProfile.Profile()
 profile.runcall(profiled_work)
 stats=pstats.Stats(profile)
 result['producer_marker_calls']=sum(v[0] for k,v in stats.stats.items() if k[2]=='producer_marker')
 result['preparation_marker_calls']=sum(v[0] for k,v in stats.stats.items() if k[2]=='preparation_marker')
 result['functions']=[k[2] for k in stats.stats]
thread=threading.Thread(target=worker);thread.start();assert ready.wait(5)
result['producer_thread']=threading.get_ident()
for i in range(500):producer_marker();time.sleep(.0001)
done.set();thread.join(5);assert not thread.is_alive()
assert result['worker_thread']!=result['producer_thread'] and result['preparation_marker_calls']>0
result['python']=sys.version;result['exclusive_worker_attribution']=result['producer_marker_calls']==0
p=Path('work/camera/prototype-runs/profile-thread-attribution.json');p.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
