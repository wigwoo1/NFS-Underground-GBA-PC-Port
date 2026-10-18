"""Private owned source-anchor draw context for queued callback integration."""
import ctypes as C,math,threading
from collections import OrderedDict
_local=threading.local()
def _clone(t,x):
 if not hasattr(_local,"types"):_local.types=OrderedDict();_local.hits=0;_local.misses=0
 key=(t,len(x));kind=_local.types.get(key)
 if kind is None:
  kind=t*len(x);_local.types[key]=kind;_local.misses+=1
  if len(_local.types)>128:_local.types.popitem(last=False)
 else:_local.types.move_to_end(key);_local.hits+=1
 return kind(*x)
def type_cache_stats():return dict(hits=getattr(_local,"hits",0),misses=getattr(_local,"misses",0),retained=len(getattr(_local,"types",{})),capacity=128)
from owned_segmented_frame_candidate import SegmentedFrame
from live_native_transaction_candidate import DrawContext
class SourceDrawContext(C.Structure):
 _fields_=[('draw',DrawContext),('a',C.c_void_p),('b',C.c_void_p),('ra',C.c_void_p),('rb',C.c_void_p),('alpha',C.c_double),('offsets',C.c_void_p),('mask',C.c_void_p),('total',C.c_uint)]
class OwnedSourceDraw:
 def __init__(self,frame,camera,models,bounds,count,a,b,ra,rb,alpha,offsets,mask,total):
  if type(frame) is not bytes and not isinstance(frame,SegmentedFrame) or len(frame)<40 or len(camera)!=12 or len(models)!=12*count or len(bounds)!=4*count or not 0<count<=144 or len(offsets)!=count+1 or not 0<=total<=32768 or len(mask)<total:raise ValueError('Invalid source draw dimensions')
  if any(len(x)!=12 for x in (a,b,ra,rb)) or not math.isfinite(alpha) or not 0<=alpha<=1 or not all(math.isfinite(x) for array in (camera,models,bounds,ra,rb) for x in array):raise ValueError('Invalid source draw values')
  if offsets[0] or offsets[-1]!=total or any(x>y for x,y in zip(offsets,offsets[1:])) or any(x not in (0,1) for x in mask[:total]):raise ValueError('Invalid source draw mask')
  if any(not isinstance(v,int) or not -2147483648<=v<=2147483647 for array in (a,b) for v in array):raise ValueError('Invalid raw camera source')
  clone=_clone
  self.frame=frame
  self.owners=[C.c_char_p(frame.prefix if isinstance(frame,SegmentedFrame) else frame),clone(C.c_double,camera),clone(C.c_double,models),clone(C.c_double,bounds),clone(C.c_int32,a),clone(C.c_int32,b),clone(C.c_double,ra),clone(C.c_double,rb),clone(C.c_uint32,offsets),clone(C.c_uint8,mask)]
  addr=lambda i:C.c_void_p.from_buffer(self.owners[i]).value if isinstance(self.owners[i],C.c_char_p) else C.addressof(self.owners[i])
  draw=DrawContext(addr(0),len(frame),addr(1),addr(2),addr(3),count,None,None,0,0,-999,0,0,0)
  self.context=SourceDrawContext(draw,addr(4),addr(5),addr(6),addr(7),alpha,addr(8),addr(9),total)
  self.segmented=isinstance(frame,SegmentedFrame)
  if self.segmented:
   self.base_owner=C.c_char_p(frame.base);self.owners.append(self.base_owner)
   self.prefix_bytes=len(frame.prefix);self.tail_bytes=len(frame.base)-frame.tail_offset
   self.tail_pointer=C.cast(self.base_owner,C.c_void_p).value+frame.tail_offset

 def attach_sky(self,sky):
  if len(sky.lower)!=15136 or len(sky.upper)!=15136 or not math.isfinite(sky.weight) or not 0<=sky.weight<=1:raise ValueError('Invalid owned sky sample')
  lower=C.create_string_buffer(bytes(sky.lower));upper=C.create_string_buffer(bytes(sky.upper));self.owners.extend((lower,upper));self.context.draw.lower=C.addressof(lower);self.context.draw.upper=C.addressof(upper);self.context.draw.skycount=15136;self.context.draw.weight=sky.weight
  return self

