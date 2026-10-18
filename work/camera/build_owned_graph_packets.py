from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
p=Path('work/camera');raw=(p/'owned-graph-materials.bin').read_bytes();offset=0;materials={}
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);n=120+(h[8] if h[9]==1 else 0);materials.setdefault(h[1],bytearray()).extend(raw[offset:offset+n]);offset+=n
raw=(p/'owned-graph-snapshots.bin').read_bytes();offset=0;checks=[];target=p/'graph-packets';target.mkdir(exist_ok=True)
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[6];start=offset+32;context=raw[start:start+896];start+=896;geometry=raw[start:start+h[4]];start+=h[4];offsets=raw[start:start+h[5]]
 packet=GraphPacket(h[1],h[2],context,geometry,offsets,bytes(materials[h[1]]));encoded=packet.encode();assert GraphPacket.decode(encoded)==packet
 (target/f'{h[1]}.ngp').write_bytes(encoded);checks.append(dict(refresh=h[1],bytes=len(encoded),descriptors=len(packet.validate())))
 offset+=928+h[4]+h[5]
(p/'owned-graph-packets.json').write_text(json.dumps(dict(result='PASS_IMMUTABLE_GRAPH_PACKET_ASSEMBLY',checks=checks),indent=2));print('PASS_IMMUTABLE_GRAPH_PACKET_ASSEMBLY',len(checks))
