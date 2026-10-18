import json,time,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph as Original
from owned_closed_graph_links_candidate import ClosedGraph as Candidate
raw=Path('work/camera/owned-closed-graph-last.bin').read_bytes()
a=Original.decode(raw);b=Candidate.decode(raw)
assert (a.epoch,a.refresh,a.objects,a.callbacks,a.associations)==(b.epoch,b.refresh,b.objects,b.callbacks,b.associations)
for name in ('context','geometry','offsets','materials'):assert getattr(a.graph,name)==getattr(b.graph,name)
assert a.graph.validate()==b.graph.validate()
times={}
for name,cls in [('original',Original),('candidate',Candidate)]:
 start=time.perf_counter_ns()
 for _ in range(100):cls.decode(raw)
 times[name]=(time.perf_counter_ns()-start)/1e6
r=dict(result='PASS_CAPTURED_GRAPH_COMPONENT',bytes=len(raw),epoch=a.epoch,refresh=a.refresh,rounds=100,decode_ms=times,scope='One captured closed graph validates identical fields and nodes. Sequential microbenchmark not live performance or fullscene proof.')
Path('work/camera/closed-graph-links-component.json').write_text(json.dumps(r,indent=2));print(r)
