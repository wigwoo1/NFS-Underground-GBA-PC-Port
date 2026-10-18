"""Owned endpoint tail references for trusted spawned-process transfer."""
import ctypes as C,struct
from owned_native_shared_write_candidate import Buffer,get_buffer,release_buffer
from owned_native_frame_join import pointer
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as borrowed_encode
from owned_segmented_frame_candidate import SegmentedFrame
TAG='owned_endpoint_tail_v1'
def encode_samples(samples,endpoints,trace=None):
 if type(endpoints)is not tuple or len(endpoints)!=2 or any(type(x)is not bytes or len(x)<40 for x in endpoints):raise ValueError('Invalid reference endpoints')
 payload=borrowed_encode(samples,trace,borrow_tails=True);tails=[];saved=0
 for tail in payload['tails']:
  reference=None
  if isinstance(tail,memoryview):
   for index,endpoint in enumerate(endpoints):
    if tail.obj is not endpoint:continue
    offset=40+struct.unpack_from('<I',endpoint,8)[0]
    if offset>len(endpoint) or len(tail)!=len(endpoint)-offset:continue
    exported=Buffer();get_buffer(tail,C.byref(exported),0)
    try:
     if exported.readonly and exported.len==len(tail) and exported.buf==pointer(endpoint)+offset:reference=(TAG,index,endpoint[:40],len(tail))
    finally:release_buffer(C.byref(exported))
    if reference is not None:break
  if reference is None:tails.append(tail)
  else:tails.append(reference);saved+=len(tail)
 payload['tails']=tails;payload['transferred_bytes']-=saved;payload['referenced_tail_bytes']=saved
 return payload

def resolve_frame(prefix,reference,endpoints):
 if type(reference)is not tuple or len(reference)!=4 or reference[0]!=TAG:raise ValueError('Invalid endpoint tail reference')
 _,index,header,length=reference
 if type(index)is not int or index not in (0,1) or type(header)is not bytes or len(header)!=40 or type(length)is not int:raise ValueError('Invalid reference fields')
 if type(endpoints)is not tuple or len(endpoints)!=2 or any(type(x)is not bytes or len(x)<40 for x in endpoints):raise ValueError('Invalid parent endpoints')
 endpoint=endpoints[index]
 if endpoint[:40]!=header:raise ValueError('Endpoint reference identity mismatch')
 offset=40+struct.unpack_from('<I',header,8)[0]
 if offset>len(endpoint) or length!=len(endpoint)-offset:raise ValueError('Endpoint reference extent mismatch')
 return SegmentedFrame(prefix,endpoint,offset)
