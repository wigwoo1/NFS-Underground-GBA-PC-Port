"""Validate immutable original-page-flip graph publication before host handoff."""
from dataclasses import dataclass
import struct
from owned_graph_packet import GraphPacket
from owned_scene_bundle import chunks
@dataclass(frozen=True)
class ClosedGraph:
 epoch:int
 refresh:int
 graph:GraphPacket
 objects:bytes
 callbacks:bytes
 associations:bytes
 @classmethod
 def decode(cls,encoded):
  raw=bytes(encoded)
  if len(raw)<40 or len(raw)>32*1024*1024:raise ValueError('Invalid closed graph length')
  h=struct.unpack_from('<8I',raw);epoch=struct.unpack_from('<Q',raw,32)[0]
  if h[:2]!=(0x3143474e,1) or not epoch or sum(h[3:])+40!=len(raw):raise ValueError('Invalid closed graph header')
  sections=[];at=40
  for n in h[3:]:sections.append(raw[at:at+n]);at+=n
  snapshot,materials,objects,callbacks,associations=sections
  if len(snapshot)<928:raise ValueError('Missing graph snapshot')
  sh=struct.unpack_from('<8I',snapshot)
  face_size=sh[7] if sh[0]==0x3353474e else 0
  if sh[0] not in (0x3253474e,0x3353474e) or sh[6]!=1 or sh[1]>h[2] or len(snapshot)!=928+sh[4]+sh[5]+face_size:raise ValueError('Invalid graph snapshot')
  graph=GraphPacket(sh[1],sh[2],snapshot[32:928],snapshot[928:928+sh[4]],snapshot[928+sh[4]:928+sh[4]+sh[5]],materials,snapshot[928+sh[4]+sh[5]:]);nodes=graph.validate();camera=graph.context[256:304];ids=set();regions=set()
  for oh,data in chunks(objects,'graph_objects'):
   if oh[0]!=0x314f474e or oh[7]!=1 or data[32:80]!=camera or oh[3] in ids or oh[6]!=oh[5]*168:raise ValueError('Invalid closed object section')
   ids.add(oh[3]);entries={struct.unpack_from('<I',data,128+i*168)[0]:struct.unpack_from('<H',data,134+i*168)[0] for i in range(oh[5])};seen=set();index=oh[4]
   while index!=65535:
    if index in seen or index not in entries:raise ValueError('Broken closed object chain')
    seen.add(index);index=entries[index]
   if seen!=entries.keys():raise ValueError('Unreachable closed object')
  if ids!=set(nodes):raise ValueError('Missing closed object region')
  for ah,data in chunks(associations,'associations'):
   if ah[0]!=0x3241534e or data[352:400]!=camera or ah[7] in regions:raise ValueError('Invalid closed association')
   regions.add(ah[7])
  for ch,data in chunks(callbacks,'callbacks'):
   if ch[0]!=0x31454f4e or data[196:244]!=camera or ch[7] not in regions:raise ValueError('Invalid closed callback join')
  return cls(epoch,h[2],graph,objects,callbacks,associations)
 def match_frame(self,frame):
  from owned_motion_pairs import _decode_records
  scene=_decode_records(frame,source_keys=False)
  if scene['epoch']!=self.epoch or scene['refresh']!=self.refresh:raise ValueError('Closed graph/frame identity mismatch')
  cameras=[bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in scene['records'] if r['kind'] in (1,2)]
  if not cameras or any(c!=self.graph.context[256:304] for c in cameras):raise ValueError('Closed graph/frame camera mismatch')
