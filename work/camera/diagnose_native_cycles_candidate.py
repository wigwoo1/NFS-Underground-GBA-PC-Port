"""Offline cycle census; DEBUG_SAVEALL never enabled in the live renderer."""
import gc,json,runpy,collections
from pathlib import Path
old=gc.get_debug();gc.collect();baseline=len(gc.garbage)
try:
 gc.set_debug(gc.DEBUG_SAVEALL)
 ns=runpy.run_path('work/camera/test_source_depth_transition_candidate.py');ns.clear();del ns
 collected=gc.collect()
 rows=gc.garbage[baseline:]
 types=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in rows)
 dictionaries=collections.Counter(tuple(sorted(str(k) for k in x.keys())) for x in rows if type(x) is dict)
 out=dict(result='MEASURED_OFFLINE_UNREACHABLE_CYCLES',collected=collected,objects=len(rows),types=types.most_common(25),dictionary_key_shapes=[dict(keys=k,count=n) for k,n in dictionaries.most_common(12)],scope='Captured four-sample preparation only. No live GC policy changes; unreachable cycles retained temporarily for type inventory.')
 Path('work/camera/prototype-runs/native-cycle-census-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:
 gc.set_debug(old);gc.garbage[baseline:]=[]
