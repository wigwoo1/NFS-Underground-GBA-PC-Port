"""Synchronous owned complete-scene batch contexts; no retained native pointers."""
import ctypes as C,math,struct,time
from owned_thread_cycles import read as thread_cycles
from live_native_transaction_candidate import DrawContext,PresentContext
P=C.c_void_p;U=C.c_uint64

def borrowed_address(owner):
 # The synchronous batch retains owners explicitly; casts create redundant cycles.
 return P.from_buffer(owner).value if isinstance(owner,C.c_char_p) else C.addressof(owner)
from pathlib import Path
_finite_lib=C.CDLL(str(Path(__file__).with_name('owned-finite-arrays.dll')))
_finite=_finite_lib.nf_owned_finite_doubles
_finite.argtypes=[C.POINTER(C.c_double),C.c_size_t];_finite.restype=C.c_int
# A bounded read-only scan takes no locks and calls no Python callbacks.
# Avoid releasing/reacquiring the GIL for small pose arrays; retain the
# releasing path for larger externally supplied arrays.
_finite_held_lib=C.PyDLL(str(Path(__file__).with_name('owned-finite-arrays.dll')))
_finite_held=_finite_held_lib.nf_owned_finite_doubles
_finite_held.argtypes=_finite.argtypes;_finite_held.restype=C.c_int
def finite_array(array):
 if isinstance(array,C.Array) and array._type_ is C.c_double:return bool((_finite_held if len(array)<=4096 else _finite)(array,len(array)))
 return all(math.isfinite(v) for v in array)
class BatchItem(C.Structure):
 _fields_=[('older',U),('newer',U),('index',U),('deadline',U),('alpha',C.c_double),('drawctx',P),('presentctx',P)]
class OwnedPresentationBatch:
 def __init__(self,epoch,rows):
  rows=tuple(rows)
  if not isinstance(epoch,int) or not 0<epoch<2**64 or not 1<=len(rows)<=8:raise ValueError('Invalid batch size/epoch')
  self.owners=[];self.draws=[];self.presents=[];items=[];self.packaging_stages=[]
  for row in rows:
   started=time.perf_counter_ns();cycles=thread_cycles()
   older,newer,index,deadline,alpha,value,sky=row
   if not (0<=older<newer<=0xffffffff and 0<=index<2**64 and 0<=deadline<2**64 and math.isfinite(alpha) and 0<=alpha<=1):raise ValueError('Invalid batch identity')
   if items and (index!=items[-1].index+1 or deadline<items[-1].deadline):raise ValueError('Unordered batch')
   frame,camera,models,bounds,detail=value
   if type(frame) is not bytes or camera is None or models is None or bounds is None:raise ValueError('Missing complete native draw owners')
   if len(frame)<40:raise ValueError('Truncated batch frame')
   header=struct.unpack_from('<6I2Q',frame)
   if header[0]!=0x3346474e or header[6]!=epoch or not older<=header[1]<=newer or header[7]!=header[1]*280896 or 40+sum(header[2:6])!=len(frame):raise ValueError('Mismatched batch frame identity/layout')
   if not math.isfinite(sky.weight) or not 0<=sky.weight<=1 or sky.destination not in (0x06002940,0x0600c940):raise ValueError('Invalid batch sky phase/placement')
   count=detail['geometry_records']
   if not isinstance(count,int) or not 0<count<=0xffffffff:raise ValueError('Invalid batch geometry count')
   if len(bounds)!=4*count or len(models)!=12*count or len(camera)!=12 or len(sky.lower)!=15136 or len(sky.upper)!=15136:raise ValueError('Invalid complete draw array sizes')
   metadata_ready=time.perf_counter_ns();metadata_cycles=thread_cycles()
   if not all(finite_array(array) for array in (camera,models,bounds)):raise ValueError('Nonfinite batch pose/bounds')
   finite_ready=time.perf_counter_ns();finite_cycles=thread_cycles()
   fb=C.c_char_p(frame);lo=C.c_char_p(sky.lower) if type(sky.lower) is bytes else C.create_string_buffer(sky.lower);hi=C.c_char_p(sky.upper) if type(sky.upper) is bytes else C.create_string_buffer(sky.upper)
   copy_ready=time.perf_counter_ns();copy_cycles=thread_cycles()
   self.owners.append((frame,camera,models,bounds,sky,fb,lo,hi))
   draw=DrawContext(borrowed_address(fb),len(frame),borrowed_address(camera),borrowed_address(models),borrowed_address(bounds),count,borrowed_address(lo),borrowed_address(hi),15136,sky.weight,-999,0,0,0)
   present=PresentContext(epoch,1,-999,0);self.draws.append(draw);self.presents.append(present)
   items.append(BatchItem(older,newer,index,deadline,alpha,C.addressof(draw),C.addressof(present)))
   completed=time.perf_counter_ns();completed_cycles=thread_cycles()
   self.packaging_stages.append(dict(index=index,frame_bytes=len(frame),geometry_records=count,array_types=[type(x).__name__ for x in (camera,models,bounds)],metadata=[started,metadata_ready,metadata_cycles-cycles],finite=[metadata_ready,finite_ready,finite_cycles-metadata_cycles],copy=[finite_ready,copy_ready,copy_cycles-finite_cycles],context=[copy_ready,completed,completed_cycles-copy_cycles]))
  self.items=(BatchItem*len(items))(*items);self.samples=(U*(8*len(items)))();self.waits=(U*(4*len(items)))();self.stages=(U*(7*len(items)))();self.completed=C.c_uint()
