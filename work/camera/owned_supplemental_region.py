"""Supplemental descriptor region construction from an owned164-byte object."""
import struct
def region(object_bytes,bounds):
 if len(object_bytes)!=164 or len(bounds)!=4:raise ValueError('Invalid supplemental source')
 if not struct.unpack_from('<H',object_bytes,10)[0]&16:return None
 descriptor=struct.unpack_from('<H',object_bytes,54)[0]
 return (descriptor,*bounds,0,0,65535)

def walk(head,objects,bounds):
 """Select supplements in original linked-list order; reject incomplete ownership."""
 seen=set();out=[]
 while head!=65535:
  if head in seen or len(seen)>=512:raise ValueError('Cyclic or oversized object chain')
  seen.add(head)
  if head not in objects:raise ValueError('Missing owned object')
  source=objects[head]
  value=region(source,bounds)
  if value is not None:out.append((head,value))
  head=struct.unpack_from('<H',source,4)[0]
 return out
