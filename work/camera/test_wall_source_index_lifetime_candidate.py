import sys,json,weakref,gc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from owned_closed_graph import ClosedGraph
from owned_graph_wall_sources_index_candidate import wall_sources
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rows=[]
def inspect(frame):
 graph=ClosedGraph.decode(Path(frame['graph']).read_bytes()).graph;ref=weakref.ref(graph);cache=[graph,None]
 wall_sources(graph,material_cache=cache,descriptors=set())
 index=cache[2];assert type(index) is tuple and all(type(row) is tuple and len(row)==6 and all(type(v) is int for v in row) for row in index)
 size=sys.getsizeof(index)+sum(sys.getsizeof(row)+sum(sys.getsizeof(v) for v in row) for row in index)
 assert len(cache)==3
 for _ in range(10):wall_sources(graph,material_cache=cache,descriptors=set());assert cache[2] is index and len(cache)==3
 refresh=graph.refresh;del graph;assert ref() is not None
 del cache;gc.collect();assert ref() is None
 return dict(refresh=refresh,index_entries=len(index),conservative_index_python_bytes=size,graph_released_after_cache_release=True)
for frame in r['wall_diagnostic_frames']:rows.append(inspect(frame))
out=dict(result='PASS_WALL_INDEX_OWNER_LIFETIME',rows=rows,maximum_index_python_bytes=max(x['conservative_index_python_bytes'] for x in rows),scope='Captured index local ownership and release; conservative object-size sum double counts shared integers, not live process footprint.')
Path('work/camera/prototype-runs/wall-source-index-lifetime.json').write_text(json.dumps(out,indent=2));print(out['result'],out['maximum_index_python_bytes'])
