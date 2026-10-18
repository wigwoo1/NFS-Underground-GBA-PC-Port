import sys,json,gc,collections,time,statistics
from pathlib import Path
mode=sys.argv[1]
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(source,'captured_setup','exec'))
from owned_endpoint_road_selection import endpoint_road_span_candidates as baseline
from owned_endpoint_road_selection_reuse_candidate import endpoint_road_span_candidates as candidate
from owned_road_asset_cache import RoadAssetCache
assets=RoadAssetCache(rom);_,_,memory,sources=assets.get(scenes[0].graph);fn=candidate if mode=='candidate' else baseline
fn(scenes[0].graph,memory,sources,table,include_empty=True)
gc.collect();assert not gc.garbage;debug=gc.get_debug();enabled=gc.isenabled();durations=[]
try:
 gc.disable();gc.set_debug(gc.DEBUG_SAVEALL)
 summaries=[]
 for i in range(20):
  begin=time.perf_counter_ns();values=fn(scenes[0].graph,memory,sources,table,include_empty=True);durations.append(time.perf_counter_ns()-begin)
  summaries.append([(x['descriptor'],x['secondary'],x['spans'],x['input_count'],x['bounds']) for x in values]);del values
 collected=gc.collect();counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 arrays=collections.Counter(getattr(x,'__module__','')+'.'+getattr(x,'__name__','') for x in gc.garbage if isinstance(x,type) and hasattr(x,'_length_'))
 out=dict(mode=mode,calls=20,collected_unreachable=collected,types=counts.most_common(),array_classes=arrays.most_common(),median_ns=statistics.median(durations),timings_ns=durations,selection_results=summaries,scope='Isolated actual captured endpoint selection, automatic GC disabled for same20calls thenDEBUG_SAVEALL census; not live gen2 latency or leak claim.')
finally:
 gc.set_debug(debug);gc.garbage.clear();gc.collect()
 if enabled:gc.enable()
assets.clear()
Path('work/camera/prototype-runs/road-reuse-cycle-'+mode+'-20261008.json').write_text(json.dumps(out,indent=2));print(mode,collected,out['median_ns'],counts.get('ctypes.CDLL',0),sum(arrays.values()))
