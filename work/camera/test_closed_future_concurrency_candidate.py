from pathlib import Path
import sys, gc, weakref, threading, json
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_closed_future_release_candidate
from owned_progressive_pair_candidate import ProgressivePair
from owned_progressive_preparation_adapter_candidate import HistoryOnlyPair
assert gc.isenabled()
rows=[]
def exercise(factory, mode):
 pair=factory(); future=pair.first
 if mode=='success': future.set_result(pair)
 elif mode=='error': pair.fail(ValueError('expected concurrent failure'))
 else: pair.close()
 barrier=threading.Barrier(5); errors=[]
 def reader():
  try:
   barrier.wait(timeout=10)
   for _ in range(400):
    current=pair.first
    assert current is future
    if mode=='success': assert current.result(timeout=1) is pair
    elif mode=='error': assert isinstance(current.exception(timeout=1),ValueError)
    else: assert current.cancelled()
  except BaseException as error: errors.append(repr(error))
 def closer():
  try:
   barrier.wait(timeout=10)
   for _ in range(400): pair.close()
  except BaseException as error: errors.append(repr(error))
 threads=[threading.Thread(target=reader) for _ in range(3)]+[threading.Thread(target=closer)]
 for thread in threads: thread.start()
 barrier.wait(timeout=10)
 for thread in threads: thread.join(timeout=15)
 assert not any(thread.is_alive() for thread in threads),'deadlock'
 assert not errors,errors
 pair.close(); ref=weakref.ref(pair)
 del pair
 if mode=='success':
  assert ref() is future.result()
  del future
  assert ref() is None,'successful pair retained after external Future release'
 return dict(mode=mode,reads=1200,concurrent_closes=400,deadlock=False)
for name,factory in [('progressive',lambda:ProgressivePair((.5,))),('history',HistoryOnlyPair)]:
 for mode in ('success','cancelled','error'):
  for repeat in range(12): rows.append(dict(kind=name,repeat=repeat,**exercise(factory,mode)))
out=dict(result='PASS_CONCURRENT_CLOSED_FUTURE_ACCESS',cases=len(rows),reads=sum(row['reads'] for row in rows),closes=sum(row['concurrent_closes'] for row in rows),normal_gc=gc.isenabled(),rows=rows,scope='Component concurrency and successful ownership release; no live cadence claim.')
Path('outputs/nfsug-native-renderer/camera-research/closed-future-concurrency-20261009.json').write_text(json.dumps(out,indent=2))
print(out['result'],out['cases'],out['reads'],out['closes'])
