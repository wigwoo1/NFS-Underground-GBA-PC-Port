"""Addressed immutable 20-byte region face dependencies for snapshot closure."""
import struct

def face_addresses(graph):
 base=struct.unpack_from('<I',graph.context,28)[0];at=0;addresses=set()
 while at<len(graph.geometry):
  _,n,_,_=struct.unpack_from('<4I',graph.geometry,at);index=struct.unpack_from('<H',graph.geometry,at+26)[0]
  if index!=65535:
   address=base+index*20
   if address+20>0x100000000:raise ValueError('Face address overflow')
   addresses.add(address)
  at+=64+n*68
 return tuple(sorted(addresses))

def encode_faces(graph,read):
 addresses=face_addresses(graph);out=[]
 for address in addresses:
  data=bytes(read(address,20))
  if len(data)!=20:raise ValueError('Incomplete face dependency')
  out.append(struct.pack('<I',address)+data)
 return struct.pack('<4I',0x3146474e,1,graph.refresh,len(out))+b''.join(out)

def decode_faces(raw,graph):
 raw=bytes(raw)
 if len(raw)<16:raise ValueError('Truncated face closure')
 h=struct.unpack_from('<4I',raw)
 if h[:3]!=(0x3146474e,1,graph.refresh) or len(raw)!=16+24*h[3]:raise ValueError('Invalid face closure')
 entries={}
 for at in range(16,len(raw),24):
  address=struct.unpack_from('<I',raw,at)[0]
  if address in entries:raise ValueError('Duplicate face dependency')
  entries[address]=raw[at+4:at+24]
 if tuple(sorted(entries))!=face_addresses(graph):raise ValueError('Incomplete face closure ownership')
 return entries
