import gc
from owned_gc_trace import CollectionTrace
before=list(gc.callbacks);enabled=gc.isenabled();thresholds=gc.get_threshold()
t=CollectionTrace(limit=1)
try:
 for i in range(2):
  cycle=[];cycle.append(cycle);del cycle;gc.collect()
 assert len(t.rows)==1 and t.dropped>=1 and all(x['end_ns']>=x['start_ns'] for x in t.rows)
finally:t.close();t.close()
assert gc.callbacks==before and gc.isenabled()==enabled and gc.get_threshold()==thresholds
print('PASS real collection capture, bounded ledger, callback cleanup; GC policy unchanged')
