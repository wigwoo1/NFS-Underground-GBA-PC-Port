"""Immutable viewport dependency joined to one closed original graph."""
from dataclasses import dataclass
import ctypes as C,struct
@dataclass(frozen=True)
class ClosedViewport:
 epoch:int
 refresh:int
 source:int
 address:int
 data:bytes
 def __post_init__(self):
  object.__setattr__(self,'data',bytes(self.data))
  if not 0<self.epoch<2**64 or not 0<=self.source<=self.refresh<2**32 or not 0<=self.address<=2**32-16 or len(self.data)!=16:raise ValueError('Invalid owned viewport')
 def validate_for(self,closed):
  if (self.epoch,self.refresh,self.source)!=(closed.epoch,closed.refresh,closed.graph.refresh) or self.address!=struct.unpack_from('<I',closed.graph.context,308)[0]:raise ValueError('Viewport graph identity mismatch')
  return self
 def bind_graph(self,closed):
  from dataclasses import replace
  self.validate_for(closed)
  return replace(closed,graph=replace(closed.graph,viewport_data=self.data))
 @property
 def horizontal(self):return struct.unpack_from('<H',self.data)[0],struct.unpack_from('<H',self.data,8)[0]
 def encode(self):return struct.pack('<4IQ16s',0x3150564e,self.refresh,self.source,self.address,self.epoch,self.data)
 @classmethod
 def decode(cls,raw):
  if len(raw)!=40:raise ValueError('Invalid viewport transport size')
  magic,refresh,source,address,epoch,data=struct.unpack('<4IQ16s',raw)
  if magic!=0x3150564e:raise ValueError('Invalid viewport transport magic')
  return cls(epoch,refresh,source,address,data)
 @classmethod
 def restore(cls,graph_bytes,viewport_bytes):
  from owned_closed_graph import ClosedGraph
  closed=ClosedGraph.decode(graph_bytes)
  viewport=cls.decode(viewport_bytes)
  return viewport.bind_graph(closed),viewport
 @classmethod
 def capture(cls,dll,closed):
  fn=dll.nf_owned_graph_closed_viewport;fn.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.c_void_p,C.c_size_t]
  address=C.c_uint32();data=C.create_string_buffer(16)
  if not fn(closed.epoch,closed.refresh,closed.graph.refresh,C.byref(address),data,16):raise ValueError('Unavailable owned viewport')
  return cls(closed.epoch,closed.refresh,closed.graph.refresh,address.value,data.raw).validate_for(closed)
