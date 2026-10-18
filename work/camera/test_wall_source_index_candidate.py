import json,struct,time,statistics,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from owned_closed_graph import ClosedGraph
from owned_graph_wall_sources import wall_sources as baseline
from owned_graph_wall_sources_index_candidate import wall_sources as candidate
raw=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
checks=[];timings=[[],[]]
for frame in raw['wall_diagnostic_frames']:
 graph=ClosedGraph.decode(Path(frame['graph']).read_bytes()).graph
 graph.validate();ids=[];at=0
 while at<len(graph.geometry):
  ident,n,_,_=struct.unpack_from('<4I',graph.geometry,at);ids.append(ident);at+=64+n*68
 caches=[[graph,None],[graph,None]]
 subsets=[None,set(),set(ids),{0xffffffff}]+[{i} for i in ids]+[set(ids[::2]),set(ids[1::2])]
 for subset in subsets:
  a=baseline(graph,validated=True,descriptors=subset,material_cache=caches[0])
  b=candidate(graph,validated=True,descriptors=subset,material_cache=caches[1])
  assert [tuple(vars(x).items()) for x in a]==[tuple(vars(x).items()) for x in b]
 try:candidate(graph,validated=True,material_cache=[object(),None])
 except ValueError:pass
 else:raise AssertionError('Owner mismatch accepted')
 for iteration in range(100):
  for which in (iteration%2,1-iteration%2):
   begin=time.perf_counter_ns()
   for ident in ids:(baseline,candidate)[which](graph,validated=True,descriptors={ident},material_cache=caches[which])
   timings[which].append(time.perf_counter_ns()-begin)
 checks.append(dict(refresh=graph.refresh,descriptors=len(ids),subsets=len(subsets)))
out=dict(result='PASS_EXACT_WALL_SOURCE_INDEX',checks=checks,baseline_median_ns=statistics.median(timings[0]),candidate_median_ns=statistics.median(timings[1]),scope='All decoded wall fields and source order on captured graphs; warm descriptor-decode microbenchmark only, not live renderer or full4K qualification.')
Path('work/camera/prototype-runs/wall-source-index-component.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
