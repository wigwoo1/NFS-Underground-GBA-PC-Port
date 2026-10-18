import json,threading,weakref,gc
from pathlib import Path
from owned_closed_graph import ClosedGraph
import owned_graph_frame_match_cache_install_candidate as cache
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());x=r['wall_diagnostic_frames'][0];encoded=Path(x['graph']).read_bytes();frame=Path(x['regenerated']).read_bytes();refs=[];sizes=[];errors=[]
def work():
 try:
  g=ClosedGraph.decode(encoded);g.match_frame(frame);g.match_frame(frame);refs.append(weakref.ref(g));sizes.append(sum(x[2] for x in cache.local.entries));assert sizes[-1]<=cache.BUDGET
 except BaseException as e:errors.append(repr(e))
t=threading.Thread(target=work);t.start();t.join(10);assert not t.is_alive() and not errors and len(refs)==1
# No owner object crosses the thread boundary except a weak reference.
gc.collect();assert refs[0]() is None
out=dict(result='PASS_THREAD_LOCAL_GRAPH_CACHE_RETIREMENT',retained_payload_bytes=sizes[0],budget_bytes=cache.BUDGET,graph_owner_released_after_thread_join=True,scope='One real scene graph and immutable frame in isolated worker thread; thread-local cache owners reclaimed. Not aggregate live working-set qualification.')
Path('work/camera/prototype-runs/graph-frame-cache-retirement-20261010.json').write_text(json.dumps(out,indent=2));print(out)
