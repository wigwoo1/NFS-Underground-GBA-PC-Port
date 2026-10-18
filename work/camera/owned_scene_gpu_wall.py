"""Regenerated GPU wall records from owned graph selection, order and clips."""
import struct
from owned_wall_projection import projected
from owned_wall_region_candidates import source_flags

def gpu_records(graph,reciprocal):
 draws,_=projected(graph,reciprocal);draws=sorted(draws,key=lambda row:(-row[0],row[2].edge))
 return encode_draws(graph.context,draws)

def _static_wall_record(context,wall):
 material=bytearray(48);struct.pack_into('<HH',material,36,wall.shift,wall.height)
 state=bytearray(260);struct.pack_into('<I',state,256,source_flags(wall))
 if len(wall.texture)>65536:raise ValueError('Wall texture exceeds current GPU ABI')
 texture_bytes=(1<<wall.shift)*wall.height if wall.shift<=10 and 0<wall.height<=1024 and (1<<wall.shift)*wall.height<=65536 else 65536
 def packed(blocks):return b''.join(struct.pack('<I',len(b))+b for b in blocks)
 prefix=struct.pack('<4I',0x3147534e,2,0,12)+packed((wall.vertices,wall.offsets,wall.animation,context[256:304],bytes(material)))
 suffix=packed((context[304:368],bytes(32),wall.texture[:texture_bytes].ljust(texture_bytes,b'\x00'),context[384:896]))
 return prefix,suffix,packed((bytes(state),))

def encode_draws(context,draws,allow_deferred=False,cache=None):
 result=[]
 for ordinal,region,wall,scratch in draws:
  if struct.unpack_from('<H',scratch,48)[0]&2 and not allow_deferred:raise ValueError('Deferred wall ordering not verified')
  key=(context,wall) if cache is not None else None
  static=cache.get(key) if cache is not None else None
  if static is None:
   static=_static_wall_record(context,wall)
   if cache is not None:
    if len(cache)>=4096:cache.clear()
    cache[key]=static
  prefix,suffix,state=static;clip=struct.pack('<4H',*region[1:5])
  record=b''.join((prefix,struct.pack('<I',len(clip)),clip,suffix,struct.pack('<I',len(scratch)),scratch,state))
  result.append((wall.vertices,record))
 return tuple(result)



def supplemental_gpu_records(bundle,reciprocal):
 from owned_supplemental_dispatch import calls
 from owned_graph_packet import GraphPacket
 from owned_graph_wall_sources import supplemental_wall_sources
 graph=GraphPacket.decode(bundle.graph);sources=supplemental_wall_sources(bundle);result=[]
 for call in calls(bundle):
  raw=call.snapshot;h=struct.unpack_from('<8I',raw)
  raw=raw[:192]+call.region+raw[208:]
  ring=b''.join(raw[976+i*140:1044+i*140] for i in range(h[4]));vertices=[ring[i*68:(i+1)*68] for i in range(h[4])]
  candidates=[w for w in sources if w.descriptor==h[3] and w.vertices[:68] in vertices]
  draws,_=projected(graph,reciprocal,(raw,candidates))
  context=raw[208:464]+raw[80:128]+raw[128:192]+raw[192:208]+raw[464:976]
  result.extend(encode_draws(context,draws,allow_deferred=True))
 return tuple(result)


