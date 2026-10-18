from pathlib import Path
from dataclasses import replace
import struct,json
from owned_graph_packet import GraphPacket
from owned_portal_traversal import traverse
exec(compile(Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0],'queue_reference_setup','exec'))
checks=[];rejections=0
for file in sorted((p/'graph-packets').glob('*.ngp')):
 raw=file.read_bytes();packet=GraphPacket.decode(raw);context=packet.context
 result=traverse(packet.validate(),struct.unpack_from('<12i',context,256),context[304:368],struct.unpack_from('<8H',context,368)[:7],reciprocal)
 assert result==scenes[packet.refresh]['expected']
 checks.append(dict(refresh=packet.refresh,regions=len(result),bytes=len(raw)))
 corrupted=bytearray(raw);corrupted[-1]^=1
 for invalid in (bytes(corrupted),raw[:-1],replace(packet,offsets=packet.offsets[:-32]).encode(),replace(packet,materials=b'').encode()):
  try:GraphPacket.decode(invalid)
  except ValueError:rejections+=1
  else:raise AssertionError('Incomplete/corrupt packet accepted')
 source=bytearray(packet.context);owned=replace(packet,context=source);source[0]^=1;assert owned.context==packet.context
assert len(checks)==8 and rejections==32
r=dict(result='PASS_IMMUTABLE_GRAPH_PACKET_VISIBILITY',scenes=8,regions=sum(x['regions'] for x in checks),invalid_packets_rejected=rejections,owned_byte_copy=True,scope='Complete portal geometry/material packet component; ordinary/supplemental object integration and live GPU transport pending.')
(p/'owned-graph-packet-tests.json').write_text(json.dumps(r,indent=2));print(r)
