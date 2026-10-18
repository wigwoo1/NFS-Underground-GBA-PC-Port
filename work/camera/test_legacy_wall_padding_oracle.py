import struct,ctypes as C,json
from dataclasses import replace
from owned_graph_wall_sources import WallSource
from owned_compact_wall_encoder_candidate import encode_draws
from owned_legacy_wall_padding import legacy_wall_padding
from owned_sample_signature import signature
w=WallSource(1,0,bytes(136),bytes(64),bytes(8),bytes(32),bytes(range(256)),4,16,0)
record=encode_draws(bytes(896),((0,(1,0,239,0,159,0,0),w,bytes(52)),))[0][1]
def split(r):
 blocks=[];at=16
 for _ in range(12):n=struct.unpack_from('<I',r,at)[0];at+=4;blocks.append(r[at:at+n]);at+=n
 return blocks
def frame(blocks,refresh=9):
 g=record[:16]+b''.join(struct.pack('<I',len(x))+x for x in blocks)
 return struct.pack('<6I2Q',0x3346474e,refresh,len(g),0,0,0,1,refresh*280896)+g
blocks=split(record);sample=(frame(blocks),(C.c_double*12)(*range(12)),None,(C.c_double*4)(0,239,0,159),dict(geometry_records=1))
expected=signature(legacy_wall_padding(sample));assert len(legacy_wall_padding(sample)[0])-len(sample[0])==65280
for i in range(12):
 b=blocks.copy();v=bytearray(b[i]);v[0]^=1;b[i]=bytes(v)
 assert signature(legacy_wall_padding((frame(b),*sample[1:])))!=expected,i
for index in (1,3):
 changed=list(sample);changed[index]=type(sample[index]).from_buffer_copy(bytes(sample[index]));changed[index][0]+=1
 assert signature(legacy_wall_padding(changed))!=expected
assert signature(legacy_wall_padding((frame(blocks,10),*sample[1:])))!=expected
changed=list(sample);changed[4]=dict(geometry_records=2);assert signature(legacy_wall_padding(changed))!=expected
for size in (0,255,257):
 b=blocks.copy();b[8]=bytes(size)
 try:legacy_wall_padding((frame(b),*sample[1:]))
 except ValueError:pass
 else:raise AssertionError('Invalid footprint accepted')
print(json.dumps(dict(result='PASS',source_block_mutations=12,pose_clip_header_detail_mutations=4,invalid_footprints=3)))
