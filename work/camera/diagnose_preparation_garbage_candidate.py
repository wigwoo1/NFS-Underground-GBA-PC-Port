"""Separate diagnostic process only: inspect unreachable preparation cycles."""
import gc,json,sys,collections,runpy
from pathlib import Path
before=gc.get_debug();initial=len(gc.garbage)
assert initial==0
try:
 gc.set_debug(gc.DEBUG_SAVEALL)
 runpy.run_path('work/camera/diagnose_preparation_heap_candidate.py',run_name='__main__')
 reclaimed=gc.collect(2)
 counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 classes=[]
 for x in gc.garbage:
  if isinstance(x,type):classes.append(dict(module=x.__module__,name=x.__qualname__))
 out=dict(result='DIAGNOSTIC_UNREACHABLE_PREPARATION_CYCLES',saved_unreachable=len(gc.garbage),final_collect_return=reclaimed,types=counts.most_common(25),classes=classes[:50],scope='Offline diagnostic process uses DEBUG_SAVEALL temporarily; alters retention and cannot qualify live timing. Settings restored; no live GC policy change.')
 Path('work/camera/prototype-runs/'+('preparation-garbage-fixed-types-20261009.json' if '--fixed-types' in sys.argv else 'preparation-garbage-20261009.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:
 gc.set_debug(before);gc.garbage.clear()
assert gc.get_debug()==before
