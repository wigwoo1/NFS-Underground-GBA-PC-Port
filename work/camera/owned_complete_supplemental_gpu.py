"""GPU wall records regenerated from independently selected complete supplemental assets."""
from owned_complete_supplemental_projection import projection_input
from owned_wall_projection import projected
from owned_scene_gpu_wall import encode_draws

def endpoint_gpu_records(closed,supplements,rom,candidates,reciprocal):
 result=[]
 for candidate in candidates:
  raw,sources=projection_input(closed,supplements,rom,candidate.descriptor,candidate.bounds)
  draws,_=projected(closed.graph,reciprocal,(raw,sources))
  context=raw[208:464]+raw[80:128]+raw[128:192]+raw[192:208]+raw[464:976]
  result.extend(encode_draws(context,draws,allow_deferred=True))
 return tuple(result)

def sampled_gpu_records(pair,alpha,rom):
 """Diagnostic wall records with continuous scissor metadata; not a complete frame."""
 import struct
 from owned_continuous_wall_visibility import sampled_edge
 from owned_wall_visibility_candidate import batch
 endpoint=1 if alpha==1 else 0
 closed=pair.scenes[endpoint];supplements=pair.supplements[endpoint]
 candidates=pair.sample(alpha);result=[]
 if alpha in (0,1):
  for c in candidates:
   for vertices,record in endpoint_gpu_records(closed,supplements,rom,(c,),pair.portal.reciprocal):
    result.append(dict(vertices=vertices,record=record,bounds=c.bounds,parent=c.parent,object=c.object,descriptor=c.descriptor,ordinal=c.ordinal,distance=c.distance))
  return tuple(result)
 _,camera,_=pair.portal.motion.sample(alpha)
 # Pair-owned bounded cache holds only immutable encoding; pose and clips stay fresh.
 if not hasattr(pair,'_supplemental_gpu_encoding_cache'):pair._supplemental_gpu_encoding_cache={}
 encoding_cache=pair._supplemental_gpu_encoding_cache
 pending=[];visibility_calls=[]
 for c in candidates:
  # Integer clip block is only a valid ABI envelope. GPU must use bounds below.
  cached=getattr(pair,'_supplemental_projection_inputs',None)
  if cached is None or cached[0] is not rom:
   cached=(rom,{})
   pair._supplemental_projection_inputs=cached
  key=(endpoint,c.descriptor)
  if key not in cached[1]:cached[1][key]=projection_input(closed,supplements,rom,c.descriptor,(0,239,0,159))
  raw,sources=cached[1][key]
  decoded=getattr(pair,'_supplemental_projection_decoded',None)
  if decoded is None or decoded[0] is not rom:
   decoded=(rom,{})
   pair._supplemental_projection_decoded=decoded
  if key not in decoded[1]:
   n=struct.unpack_from('<I',raw,16)[0]
   ring=b''.join(raw[976+i*140:1044+i*140] for i in range(n))
   context=raw[208:464]+raw[80:128]+raw[128:192]+raw[192:208]+raw[464:976]
   decoded[1][key]=(ring,context)
  ring,context=decoded[1][key]
  for w in sources:
   edge=sampled_edge(w,ring,pair.scenes[0].graph.context[256:304],pair.scenes[1].graph.context[256:304],camera,pair.portal.endpoints,alpha)
   if edge is None:continue
   base=raw[1076+w.edge*140:1108+w.edge*140]
   visibility_calls.append((w,raw[32:80],edge,closed.graph.context[304:368],c.bounds,base,pair.portal.reciprocal))
   pending.append((c,raw,w))
 for (c,raw,w),visibility in zip(pending,batch(visibility_calls)):
  if not visibility.visible:continue
  # Scratch is a transport placeholder; this GPU path consumes raw world quad.
  scratch=bytearray(52);struct.pack_into('<H',scratch,48,visibility.flags)
  region=(c.descriptor,0,239,0,159,0,0)
  context=pair._supplemental_projection_decoded[1][(endpoint,c.descriptor)][1]
  vertices,record=encode_draws(context,((0,region,w,bytes(scratch)),),allow_deferred=True,cache=encoding_cache)[0]
  result.append(dict(vertices=vertices,record=record,bounds=c.bounds,parent=c.parent,object=c.object,descriptor=c.descriptor,ordinal=c.ordinal,distance=c.distance))
 return tuple(result)
