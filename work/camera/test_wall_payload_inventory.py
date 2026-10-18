"""Measure actual immutable wall-source payload reuse; no renderer mutation."""
import sys,json,hashlib,time,statistics,tracemalloc
from pathlib import Path
sys.argv=[__file__,'work/camera/prototype-runs/child-scene-1791637661169682300']
ns={};exec(Path('work/camera/test_current_wall_record_scopes.py').read_text().split('from owned_progressive_source_samples_candidate')[0],ns)
from owned_graph_wall_sources import wall_sources
results=[];payloads=[]
prepared=ns["PreparedWorldMotion"](*ns["frames"],*ns["scenes"],ns["history"],ns["roads"],ns["rom"])
queue=prepared.pair.portal.sample(.2)
needed={x[0] for x in queue if not x[5]&8 and x[1]<=x[2] and x[3]<=x[4]}
try:
 for scene in ns['scenes']:
  graph=scene.graph.graph;timings={False:[],True:[]};cached=[graph,None]
  reference=wall_sources(graph,descriptors=needed,material_cache=cached)
  sig=lambda rows:hashlib.sha256(b''.join(str((x.descriptor,x.edge,x.shift,x.height,x.address)).encode()+x.vertices+x.offsets+x.animation+x.resolved+x.texture for x in rows)).hexdigest()
  expected=sig(reference)
  for i in range(20):
   for reuse in ((False,True) if i%2==0 else (True,False)):
    begin=time.perf_counter_ns();rows=wall_sources(graph,descriptors=needed,material_cache=cached if reuse else [graph,None]);timings[reuse].append(time.perf_counter_ns()-begin);assert sig(rows)==expected
  unique={id(x.texture):x.texture for x in reference};contents={hashlib.sha256(x).hexdigest() for x in unique.values()};payloads.append(contents)
  tracemalloc.start();rows=wall_sources(graph,descriptors=needed,material_cache=[graph,None]);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();assert sig(rows)==expected
  results.append(dict(refresh=graph.refresh,walls=len(reference),geometry_bytes=len(graph.geometry),material_bytes=len(graph.materials),unique_texture_owners=len(unique),unique_texture_bytes=sum(map(len,unique.values())),texture_bytes_referenced=sum(len(x.texture) for x in reference),uncached_median_ms=statistics.median(timings[False])/1e6,cached_material_median_ms=statistics.median(timings[True])/1e6,uncached_peak_bytes=peak,signature=expected))
finally:prepared.close();ns['history'].close()
out=dict(result='PASS_WALL_PAYLOAD_INVENTORY',endpoints=results,needed_descriptors=sorted(needed),equal_texture_content_between_endpoints=len(payloads[0]&payloads[1]),scope='Two validated saved endpoints, alpha.2 actual portal descriptor subset, full returned wall bytes exact. Cached timing uses existing per-graph material cache; no new optimization, no live cadence qualification.')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-payload-inventory-20261010');p.mkdir(exist_ok=True);(p/'subset-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
