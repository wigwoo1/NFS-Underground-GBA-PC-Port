import sys,json,time,statistics,tracemalloc
from pathlib import Path
sys.argv=[__file__,'work/camera/prototype-runs/child-scene-1791637661169682300']
ns={};exec(Path('work/camera/test_current_wall_record_scopes.py').read_text().split('from owned_progressive_source_samples_candidate')[0],ns)
from owned_graph_wall_sources import wall_sources as original
from owned_wall_lazy_texture_candidate import wall_sources as candidate,TextureSpan
prepared=ns['PreparedWorldMotion'](*ns['frames'],*ns['scenes'],ns['history'],ns['roads'],ns['rom'])
queue=prepared.pair.portal.sample(.2);needed={x[0] for x in queue if not x[5]&8 and x[1]<=x[2] and x[3]<=x[4]}
results=[]
try:
 for scene in ns['scenes']:
  graph=scene.graph.graph;reference=original(graph,descriptors=needed);timings={False:[],True:[]};alloc={}
  for i in range(40):
   for lazy in ((False,True) if i%2==0 else (True,False)):
    cache=[graph,None];f=candidate if lazy else original;start=time.perf_counter_ns();rows=f(graph,descriptors=needed,material_cache=cache);timings[lazy].append(time.perf_counter_ns()-start)
    assert rows==reference
    # Expanding the same owner cache must decode all remaining textures exactly.
    assert f(graph,material_cache=cache)==original(graph)
    assert f(graph,descriptors=set(),material_cache=cache)==()
  for lazy in (False,True):
   tracemalloc.start();cache=[graph,None];rows=(candidate if lazy else original)(graph,descriptors=needed,material_cache=cache);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();assert rows==reference
   spans={id(v[2]):v[2] for v in cache[1].values() if isinstance(v[2],TextureSpan)}
   alloc[lazy]=dict(current_bytes=current,peak_bytes=peak,lazy_spans=len(spans),resolved_spans=sum(x.value is not None for x in spans.values()),resolved_bytes=sum(len(x.value) for x in spans.values() if x.value is not None))
  results.append(dict(refresh=graph.refresh,walls=len(reference),baseline_median_ms=statistics.median(timings[False])/1e6,candidate_median_ms=statistics.median(timings[True])/1e6,allocation=alloc))
finally:prepared.close();ns['history'].close()
out=dict(result='PASS_LAZY_WALL_TEXTURE_COMPONENT',endpoints=results,scope='40 alternating rounds each captured endpoint, actual portal subset and incremental all-descriptor cache expansion; complete dataclass equality, not current fullscene/GPU/live qualification')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-lazy-textures-20261010');p.mkdir(exist_ok=True);(p/'component.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
