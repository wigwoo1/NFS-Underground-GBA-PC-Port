import json
from pathlib import Path
from dataclasses import replace
from owned_closed_graph import ClosedGraph
from owned_closed_viewport import ClosedViewport as Original
from owned_closed_viewport_cache_candidate import ClosedViewport as Candidate
import struct
c=ClosedGraph.decode(Path('work/camera/owned-closed-graph-last.bin').read_bytes());address=struct.unpack_from('<I',c.graph.context,308)[0];checks=[]
for names in ((),('_parsed_graph',),('_parsed_graph','_validated_graph','descriptor_links')):
 g=replace(c.graph);g.validate();g.descriptor_links
 for key in ('_parsed_graph','_validated_graph','descriptor_links'):
  if key not in names:g.__dict__.pop(key,None)
 closed=replace(c,graph=g);args=(c.epoch,c.refresh,g.refresh,address,bytes(16));a=Original(*args).bind_graph(closed);b=Candidate(*args).bind_graph(closed)
 assert a==b and a.graph.validate()==b.graph.validate() and a.graph.descriptor_links==b.graph.descriptor_links
 checks.append(list(names))
Path('work/camera/viewport-cache-presence-tests.json').write_text(json.dumps(dict(result='PASS',cache_sets=checks,scope='One captured graph, synthetic viewport, absent/partial/full validation caches; original and candidate outcomes exact.'),indent=2));print('PASS three cache-presence cases')
