"""Identify external car draws from original source, descriptor and exact builder pose."""
import struct
from types import MappingProxyType
from owned_motion_pairs import records
from owned_scene_bundle import chunks
from owned_object_dispatch import select
from owned_object_filter import depth_distance
from owned_external_model_projection import external_model_matrix

def external_model_owners(closed,builders,frame,rom,decoded_rows=None):
 closed.match_frame(frame);state=closed.graph.context[:256];base=struct.unpack_from('<I',state,60)[0]
 sources={}
 for h,raw in chunks(closed.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168]
   sources.setdefault(index,[]).append(source)
 candidates=[]
 for (address,matrix),values in builders.records.items():
  if address<base or (address-base)%164:continue
  index=(address-base)//164
  if index not in sources:continue
  valid=[b for b in values if b.refresh<=closed.refresh]
  if not valid:continue
  b=valid[-1]
  if not b.external_enabled or not struct.unpack_from('<H',b.source,10)[0]&32:continue
  model=struct.unpack_from('<h',b.source,54)[0]
  if not all(struct.unpack_from('<h',s,54)[0]==model and s[140:144]==b.source[140:144] for s in sources[index]):raise ValueError('External source identity changed')
  if b.source[136]>=64:raise ValueError('Invalid original external builder allocation')
  depth=depth_distance(b.source,b.camera)[0];dispatch=select(b.source,state,depth)
  if dispatch['kind']!='model':continue
  offset=dispatch['descriptor']-0x08000000
  if not 0<=offset<=len(rom)-40:raise ValueError('External descriptor outside owned ROM')
  candidates.append((index,rom[offset:offset+40],external_model_matrix(b)))
 owners={}
 for index,row in enumerate(records(frame)['records'] if decoded_rows is None else decoded_rows):
  if row['kind']!=3:continue
  matches={owner for owner,descriptor,pose in candidates if bytes(row['blocks'][1])==descriptor and bytes(row['blocks'][2])==pose}
  if len(matches)>1:raise ValueError('Ambiguous external draw ownership')
  if matches:owners[index]=matches.pop()
 if len(set(owners.values()))!=len(owners):raise ValueError('Repeated external source draw')
 return MappingProxyType(owners)
