from pathlib import Path
import sys,weakref,gc,json
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_closed_future_release_candidate
from owned_progressive_pair_candidate import ProgressivePair
from owned_progressive_preparation_adapter_candidate import HistoryOnlyPair
assert gc.isenabled();rows=[]
for name,factory in [('progressive',lambda:ProgressivePair((.5,))),('history',HistoryOnlyPair)]:
 pair=factory();future=pair.first;assert pair.first is future;future.set_result(pair);pair.close();pair.close();assert pair.first is future and future.result() is pair
 ref=weakref.ref(pair);del pair;assert ref() is future.result();del future;assert ref() is None
 pair=factory();pair.first.set_result(pair);pair.close();future=pair.first;assert future.result() is pair;assert pair.first is future;pair.close();del future;ref=weakref.ref(pair);del pair;assert ref() is None
 pair=factory();future=pair.first;pair.close();pair.close();assert future.cancelled() and pair.first is future
 pair=factory();future=pair.first;error=ValueError('expected');pair.fail(error);pair.close();assert future.exception() is error and pair.first is future
 rows.append(dict(kind=name,successful_closed_pair_reclaimed_without_collect=True,external_future_identity_and_result_preserved=True,recreated_closed_result=True,pending_cancelled=True,error_preserved=True,double_close=True))
out=dict(result='PASS_CLOSED_FUTURE_BACKREFERENCE_RELEASE',rows=rows,scope='Successful closed pairs only; error traceback cycles remain separate. Component ownership, not live cadence proof.')
Path('outputs/nfsug-native-renderer/camera-research/closed-future-release-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
