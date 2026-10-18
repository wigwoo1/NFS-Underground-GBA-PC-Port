import json,struct
from pathlib import Path
from dataclasses import replace
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791283570030404100.json').read_text());slots=[]
for scene in r['model_scene_captures']:
 graph=ClosedGraph.decode(Path(scene['graph']).read_bytes());raw=bytearray(Path(scene['current-sources']).read_bytes());owned=OwnedModelSources.decode(raw,graph);base=struct.unpack_from('<I',graph.graph.context,60)[0];address=base+31*164;source=owned.sources[address];slots.append(source[136]);raw[-1]^=1;assert owned.sources[address]==source
 for altered in (replace(graph,epoch=graph.epoch+1),replace(graph,refresh=graph.refresh+1)):
  try:OwnedModelSources.decode(Path(scene['current-sources']).read_bytes(),altered)
  except ValueError:pass
  else:raise AssertionError('Unpaired source accepted')
 try:owned.sources[address]=b''
 except TypeError:pass
 else:raise AssertionError('Mutable source map')
 print(dict(display=owned.refresh,source=owned.source_refresh,slot=source[136],object31_retained=True))
assert slots==[0,255],slots
print('PASS: aligned source closure, deactivation, immutable bytes/map, epoch/display mismatch rejection')
