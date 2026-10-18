import sys,json,time,statistics,weakref,gc,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
import owned_scenery_thread_library_install_candidate as candidate
from owned_scenery_motion import PreparedSceneryMotion
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0];exec(compile(setup,'captured-scenery-fixture','exec'));prepared.close()
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
try:
 prepared.sample(.5);pairs=tuple(prepared.pair._scenery_record_pairs.values());assert pairs
 plan=prepared.pair.portal.motion.arguments[0];arguments=(pairs,plan['camera_older'],plan['camera_newer'])
 old=PreparedSceneryMotion.__new__(PreparedSceneryMotion);candidate.original(old,*arguments)
 new=PreparedSceneryMotion(*arguments);other=PreparedSceneryMotion(*arguments)
 assert new._lib is other._lib and new._basis is not other._basis and new._prepared is not other._prepared
 checks=0
 for key in old._prepared:
  for i in range(101):assert old.matrix(key,i/100)==new.matrix(key,i/100);checks+=1
 rows=[]
 for trial in range(8):
  mode='original' if trial%2==0 else 'thread_local';init=candidate.original if mode=='original' else PreparedSceneryMotion.__init__;gc.collect();times=[];refs=[]
  for i in range(20):
   value=PreparedSceneryMotion.__new__(PreparedSceneryMotion);begin=time.perf_counter_ns();init(value,*arguments);times.append(time.perf_counter_ns()-begin);refs.append(weakref.ref(value._lib));value=None
  gc.collect();dead=sum(x() is None for x in refs);assert dead==(20 if mode=='original' else 0)
  rows.append(dict(mode=mode,median_ns=statistics.median(times),dead_wrapper_refs=dead))
 # Basis mutation must not reach another prepared scene.
 before=other._basis[0].x;new._basis[0].x=123;assert other._basis[0].x==before
 barrier=threading.Barrier(3);ids=[];errors=[]
 def run():
  try:library=candidate.scenery_library();ids.append(id(library));barrier.wait(5);barrier.wait(5)
  except BaseException as e:errors.append(str(e));barrier.abort()
 threads=[threading.Thread(target=run) for _ in range(2)]
 for t in threads:t.start()
 barrier.wait(5);assert len(set(ids+[id(new._lib)]))==3;barrier.wait(5)
 for t in threads:t.join(5);assert not t.is_alive()
 assert not errors
 out=dict(result='PASS_CAPTURED_SCENERY_POSE_THREAD_LIBRARY',objects=len(pairs),matrix_checks=checks,private_scene_basis=True,thread_wrappers_distinct=True,cost_trials=rows,scope='Actual captured scenery pairs at101 fractions, exact same numeric matrices, private pose/basis ownership and three-thread wrapper isolation. Eight alternating constructor trials; no live cadence benefit claim.')
 Path('work/camera/prototype-runs/scenery-thread-library-matrices-cost-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:prepared.close();history.close()



