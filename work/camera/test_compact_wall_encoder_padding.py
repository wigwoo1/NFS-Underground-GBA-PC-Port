import struct,json
from dataclasses import replace
from owned_graph_wall_sources import WallSource
from owned_scene_gpu_wall import encode_draws as legacy
from owned_compact_wall_encoder_candidate import encode_draws as compact
w=WallSource(1,0,bytes(136),bytes(64),bytes(8),bytes(32),b'',4,16,0)
def blocks(record):
 out=[];at=16
 for i in range(12):n=struct.unpack_from('<I',record,at)[0];at+=4;out.append(record[at:at+n]);at+=n
 return out
for texture in (b'',bytes(range(30)),bytes(range(256)),bytes(range(256))*256):
 wall=replace(w,texture=texture);draw=((0,(1,0,239,0,159,0,0),wall,bytes(52)),)
 a=blocks(legacy(bytes(896),draw)[0][1]);b=blocks(compact(bytes(896),draw)[0][1]);assert len(b[8])==256 and b[8]==a[8][:256]
 assert all(a[i]==b[i] for i in range(12) if i!=8)
print('PASS four short/full/oversized-footprint texture sources preserve sampled pixels and all other blocks')
