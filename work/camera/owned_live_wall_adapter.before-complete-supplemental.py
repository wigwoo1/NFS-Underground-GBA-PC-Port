"""Live wall reconstruction from immutable paired raw scene snapshots."""
import struct
from types import SimpleNamespace
from collections import defaultdict,deque
from owned_scene_gpu_wall import gpu_records,encode_draws
from owned_wall_projection import projected
from owned_graph_wall_sources import supplemental_wall_sources
from owned_scene_bundle import chunks
from owned_motion_pairs import records

def reconstruct(frame,closed,supplements,reciprocal):
 if (closed.epoch,closed.refresh)!=(supplements.epoch,supplements.refresh):raise ValueError('Unpaired wall scene')
 graph=closed.graph;generated=list(gpu_records(graph,reciprocal))
 proxy=SimpleNamespace(supplements=supplements.geometry,textures=supplements.textures,validate=lambda:None)
 sources=supplemental_wall_sources(proxy)
 for h,raw in chunks(supplements.geometry,'supplements'):
  ring=b''.join(raw[976+i*140:1044+i*140] for i in range(h[4]));vertices=[ring[i*68:(i+1)*68] for i in range(h[4])]
  selected=[w for w in sources if w.descriptor==h[3] and w.vertices[:68] in vertices]
  draws,_=projected(graph,reciprocal,(raw,selected));context=raw[208:464]+raw[80:128]+raw[128:192]+raw[192:208]+raw[464:976]
  generated.extend(encode_draws(context,draws,allow_deferred=True))
 available=defaultdict(deque)
 for vertices,encoded in generated:
  at=16;clip=None
  for i in range(12):
   n=struct.unpack_from('<I',encoded,at)[0];at+=4
   if i==5:clip=encoded[at:at+n]
   at+=n
  available[(vertices,clip)].append(encoded)
 geometry=[];count=0
 for row in records(frame)['records']:
  b=[bytes(x) for x in row['blocks']]
  if row['kind']==2:
   key=(b[0],b[5])
   if not available[key]:raise ValueError('Owned wall selection/clip mismatch')
   geometry.append(available[key].popleft());count+=1
  else:geometry.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+x for x in b))
 if any(available.values()):raise ValueError('Extra owned wall selections')
 header=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+header[2]:];g=b''.join(geometry);header[2]=len(g)
 return struct.pack('<6I2Q',*header)+g+tail,count
