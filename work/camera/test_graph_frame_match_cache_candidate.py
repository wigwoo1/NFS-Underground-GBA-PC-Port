import json,struct
from pathlib import Path
from dataclasses import replace
from owned_closed_graph import ClosedGraph
import owned_graph_frame_match_cache_install_candidate as cache
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());n=0
for x in r['wall_diagnostic_frames']:
 graph=ClosedGraph.decode(Path(x['graph']).read_bytes());frame=Path(x['regenerated']).read_bytes()
 cache.original(graph,frame);graph.match_frame(frame);graph.match_frame(frame);n+=1
 # Different immutable frame owner must be revalidated, including equal bytes.
 equal=bytes(bytearray(frame));before=cache.stats['validated'];graph.match_frame(equal);assert cache.stats['validated']==before+1
 bad=bytearray(frame);bad[4]^=1
 try:graph.match_frame(bytes(bad))
 except ValueError:pass
 else:raise AssertionError('Changed frame accepted')
 badgraph=replace(graph,refresh=graph.refresh+1)
 try:badgraph.match_frame(frame)
 except ValueError:pass
 else:raise AssertionError('Changed graph accepted')
assert cache.stats['hits']>=n
assert len(cache.local.entries)<=2 and sum(x[2] for x in cache.local.entries)<=cache.BUDGET
mutable=bytearray(frame);before=cache.stats['uncached'];graph.match_frame(mutable);assert cache.stats['uncached']==before+1
mutable[4]^=1
try:graph.match_frame(mutable)
except ValueError:pass
else:raise AssertionError('Mutable changed frame reused')
out=dict(result='PASS_EXACT_IMMUTABLE_GRAPH_FRAME_MATCH_CACHE',frames=n,stats=cache.stats,scope='Retained original/regenerated scene frame validity, exactowner hits, equal-byte replacement revalidation and changed-frame/graph rejection. No whole-game speedup or native byte-compare removal.')
Path('work/camera/prototype-runs/graph-frame-cache-component-20261010.json').write_text(json.dumps(out,indent=2));print(out)
