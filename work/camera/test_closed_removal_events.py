"""Removal events are scene owned and cannot leak future timestamps."""
import json,struct,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
r=json.loads(Path(sys.argv[1]).read_text());checks=[]
for scene in r['model_scene_captures']:
 graph=ClosedGraph.decode(Path(scene['graph']).read_bytes());raw=Path(scene['current-sources']).read_bytes();packet=OwnedModelSources.decode(raw,graph);base=struct.unpack_from('<I',graph.graph.context,60)[0];address=base+31*164
 checks.append((packet.source_refresh,packet.sources[address][136],packet.removals.get(address)))
 count=struct.unpack_from('<I',raw,16)[0]
 for i in range(count):
  if struct.unpack_from('<I',raw,32+i*176)[0]!=address:continue
  bad=bytearray(raw);struct.pack_into('<2I',bad,200+i*176,packet.source_refresh+1,0x0801e4c2)
  try:OwnedModelSources.decode(bad,graph)
  except ValueError:pass
  else:raise AssertionError('Future removal accepted')
print(checks)
assert checks[-1]==(10035,255,(10035,0x0801e4c2)),checks
print('PASS: exact original source31 removal is paired to source10035, future event rejected')
