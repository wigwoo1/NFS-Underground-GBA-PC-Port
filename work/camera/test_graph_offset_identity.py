from pathlib import Path
from dataclasses import replace
from owned_graph_packet import GraphPacket
from owned_sampled_graph_wall_visibility import graph_offset_rings
folder=Path('work/camera/prototype-runs/fullscene-failure-1791274597237012700')
a=GraphPacket.decode((folder/'older.graph.bin').read_bytes());b=GraphPacket.decode((folder/'newer.graph.bin').read_bytes())
assert a.offsets!=b.offsets and graph_offset_rings(a)==graph_offset_rings(b)
changed=bytearray(b.offsets);changed[0]^=1
assert graph_offset_rings(a)!=graph_offset_rings(replace(b,offsets=bytes(changed)))
print('PASS serialized-order transition preserves descriptor-owned offsets; actual byte mutation detected')
