"""Component ownership audit; normal GC remains enabled."""
from pathlib import Path
import sys,gc,weakref,json
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_progressive_pair_candidate import ProgressivePair
from owned_progressive_preparation_adapter_candidate import HistoryOnlyPair
assert gc.isenabled();rows=[]
for label,factory in [('progressive',lambda:ProgressivePair((.5,))),('history_only',HistoryOnlyPair)]:
 gc.collect();pair=factory();pair.first.set_result(pair);future=pair.first;reference=weakref.ref(pair)
 pair.close();assert future.result() is pair and not pair.samples if label=='progressive' else future.result() is pair
 assert pair.first._result is pair and gc.is_tracked(pair) and gc.is_tracked(pair.first)
 del pair;assert reference() is not None
 del future;retained_before_gc=reference() is not None
 collected=gc.collect();assert reference() is None
 rows.append(dict(kind=label,closed_pair_future_self_cycle=True,external_future_preserves_result=True,retained_after_external_future_release_before_gc=retained_before_gc,reclaimed_after_collection=True,collected_objects=collected))
out=dict(result='PASS_CLOSED_PREPARATION_FUTURE_CYCLE_AUDIT',rows=rows,scope='Two component pair owners with completed Future result; does not identify all live collected objects or prove cycle removal fixes fullscene cadence. Normal GC enabled.')
Path('outputs/nfsug-native-renderer/camera-research/closed-preparation-future-cycle-20261009.json').write_text(json.dumps(out,indent=2));print(out)
