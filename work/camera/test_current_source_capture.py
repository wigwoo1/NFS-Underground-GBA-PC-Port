import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791283448024037100.json').read_text())
for scene in r['model_scene_captures']:
 raw=Path(scene['current-sources']).read_bytes();h=struct.unpack_from('<6IQ',raw);graph=ClosedGraph.decode(Path(scene['graph']).read_bytes()).graph;base=struct.unpack_from('<I',graph.context,60)[0];found=[]
 for i in range(h[4]):
  address=struct.unpack_from('<I',raw,32+i*168)[0];source=raw[36+i*168:200+i*168]
  if address==base+31*164:found.append(dict(refresh=scene['refresh'],capture_refresh=h[3],object=31,slot=source[136],model=struct.unpack_from('<h',source,54)[0],position=struct.unpack_from('<3i',source,12),association_fields=struct.unpack_from('<4H',source)))
 assert len(found)==1,'Missing current source31'
 print(found)
print('PASS current source31 retained across both closure snapshots')

