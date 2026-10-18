import json
from pathlib import Path
from dataclasses import replace
from owned_closed_graph import ClosedGraph
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());c=ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes());g=c.graph;first=g.graph();assert g.graph() is first and g.validate() is g.validate()
try:first[0][g.root]=(b'',0,0)
except TypeError:pass
else:raise AssertionError('Cached geometry mutable')
try:replace(g,materials=g.materials[:-1]).validate()
except ValueError:pass
else:raise AssertionError('Malformed new snapshot bypassed validation')
Path('work/camera/immutable-graph-cache-tests.json').write_text(json.dumps(dict(result='PASS_INSTANCE_OWNED_GRAPH_CACHE',immutable_mapping=True,new_snapshot_validation=True),indent=2));print('PASS_INSTANCE_OWNED_GRAPH_CACHE')
