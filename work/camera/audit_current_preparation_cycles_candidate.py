"""Isolated current captured workload cycle inventory; DEBUG_SAVEALL restored."""
import gc,runpy,json,collections,types,contextlib,io,statistics
from pathlib import Path
saved=gc.get_debug();gc.collect();assert not gc.garbage
try:
 gc.set_debug(gc.DEBUG_SAVEALL)
 with contextlib.redirect_stdout(io.StringIO()):namespace=runpy.run_path('work/camera/test_precomputed_decode_release_candidate.py',run_name='__main__')
 del namespace
 collected=gc.collect()
 counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 arrays=collections.Counter((getattr(x,'__module__',''),getattr(x,'__name__',''),getattr(x,'_length_',None)) for x in gc.garbage if isinstance(x,type) and hasattr(x,'_length_'))
 functions=collections.Counter(x.__code__.co_filename+':'+x.__qualname__ for x in gc.garbage if isinstance(x,types.FunctionType))
 out=dict(result='CURRENT_CAPTURED_UNREACHABLE_INVENTORY',collected=collected,types=counts.most_common(20),array_classes=[dict(module=k[0],name=k[1],length=k[2],count=n) for k,n in arrays.most_common()],functions=functions.most_common(15),scope='Current captured test including test infrastructure; not live generation2 object provenance.')
finally:
 gc.set_debug(saved);gc.garbage.clear();gc.collect()
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791514840300785600.json').read_text())
rows=r['world_preparation_stage_samples']; stages={}
for row in rows:
 for stage in row['construct_stages']:
  stages.setdefault(stage['name'],[]).append(stage['wall_ns']/1e6)
out['retained_live_preparation_stages']={k:dict(count=len(v),median_ms=statistics.median(v),max_ms=max(v)) for k,v in stages.items()}
out['retained_live_preparation_totals']={k:dict(median_ms=statistics.median(row[k]/1e6 for row in rows),max_ms=max(row[k]/1e6 for row in rows)) for k in ('construct_advance_ns','precompute_ns')}
Path('work/camera/prototype-runs/current-preparation-cycle-stages-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
