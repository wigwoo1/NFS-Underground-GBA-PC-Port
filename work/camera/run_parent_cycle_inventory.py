"""Diagnostic cycle inventory only; saved garbage invalidates pacing comparisons."""
import gc,runpy,json,collections,sys
from pathlib import Path
before=gc.get_debug();gc.set_debug(before|gc.DEBUG_SAVEALL)
try:
 runpy.run_path('work/camera/run_process_transport_dedup_candidate.py',run_name='__main__')
 gc.collect()
 counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 edges=collections.Counter()
 for x in gc.garbage:
  for y in gc.get_referents(x):edges[(type(x).__module__+'.'+type(x).__qualname__,type(y).__module__+'.'+type(y).__qualname__)]+=1
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/parent-cycle-inventory-20261007');cp.mkdir(exist_ok=True)
 out=dict(objects=len(gc.garbage),types=counts.most_common(30),edges=[dict(source=a,target=b,count=n) for (a,b),n in edges.most_common(30)],scope='Diagnostic DEBUG_SAVEALL retains otherwise collectible garbage; counts locate cycles but do not establish production timing or exclusive source attribution')
 (cp/'inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
finally:gc.set_debug(before);gc.garbage.clear()
