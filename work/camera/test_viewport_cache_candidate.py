import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_viewport import ClosedViewport as Original
from owned_closed_viewport_cache_candidate import ClosedViewport as Candidate
closed=ClosedGraph.decode(Path('work/camera/owned-closed-graph-last.bin').read_bytes());original_graph=closed.graph;nodes=original_graph.validate();links=original_graph.descriptor_links
address=struct.unpack_from('<I',original_graph.context,308)[0]
args=(closed.epoch,closed.refresh,original_graph.refresh,address,bytes(16))
a=Original(*args).bind_graph(closed);b=Candidate(*args).bind_graph(closed)
assert a==b and a.graph.validate()==b.graph.validate() and a.graph.descriptor_links==b.graph.descriptor_links
assert b.graph is not original_graph and b.graph.validate() is nodes and b.graph.descriptor_links is links
assert original_graph.viewport_data==b'' and b.graph.viewport_data==bytes(16)
for cls in (Original,Candidate):
 try:cls(closed.epoch+1,*args[1:]).bind_graph(closed)
 except ValueError:pass
 else:raise AssertionError('Invalid epoch accepted')
times={'original':[],'candidate':[]}
for n in range(20):
 for label,cls in ([('original',Original),('candidate',Candidate)] if n%2==0 else [('candidate',Candidate),('original',Original)]):
  start=time.perf_counter_ns()
  for _ in range(100):cls(*args).bind_graph(closed).graph.validate()
  if n>=4:times[label].append((time.perf_counter_ns()-start)/100/1e6)
r=dict(result='PASS_VIEWPORT_VALIDATION_CACHE_COMPONENT',median_bind_validate_ms={k:statistics.median(v) for k,v in times.items()},rounds=times,scope='One captured immutable graph, synthetic16-byte viewport, identical validated nodes/link caches, independent packet and unchanged original viewport, invalid epoch rejection. Not live/fullscene timing proof.')
Path('work/camera/viewport-cache-component.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k!='rounds'})
