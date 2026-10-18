"""Immutable original sky copy metadata and owned source bytes; no GPU sampling."""
from dataclasses import dataclass
import struct
from owned_sky_scroll import source_offset
from owned_sky_sampler import SkyAsset
HEADER=struct.Struct('<4sI Q 8I i I')
@dataclass(frozen=True)
class SkyBoundary:
 epoch:int
 refresh:int
 angle:int
 width:int
 height:int
 center:int
 source:int
 asset_origin:int
 destination:int
 indices:bytes
 def __post_init__(self):
  object.__setattr__(self,'indices',bytes(self.indices))
  if not 0<self.epoch<2**64 or not 0<=self.refresh<2**32 or not 0<=self.angle<2**32:raise ValueError('Invalid sky identity')
  if self.width!=240 or self.height!=64:raise ValueError('Unsupported sky dimensions')
  if self.source!=self.asset_origin+source_offset(self.angle,self.width,self.center):raise ValueError('Sky phase/source mismatch')
  if not 0x08000000<=self.asset_origin<0x0a000000:raise ValueError('Invalid sky asset origin')
  if self.destination not in (0x06002940,0x0600c940):raise ValueError('Unsupported vertical sky placement')
  if len(self.indices)!=15136:raise ValueError('Incomplete original sky copy bytes')
 @property
 def identity(self):return self.epoch,self.refresh
 def encode(self):
  return HEADER.pack(b'NFSK',1,self.epoch,self.refresh,self.angle,self.width,self.height,self.source,self.asset_origin,self.destination,len(self.indices),self.center,0)+self.indices
 @classmethod
 def decode(cls,data):
  if len(data)<HEADER.size:raise ValueError('Truncated sky header')
  magic,version,epoch,refresh,angle,width,height,source,origin,destination,count,center,reserved=HEADER.unpack_from(data)
  if magic!=b'NFSK' or version!=1 or reserved or count!=len(data)-HEADER.size:raise ValueError('Invalid sky packet')
  return cls(epoch,refresh,angle,width,height,center,source,origin,destination,bytes(data[HEADER.size:]))
 def plane(self):
  # Complete original contiguous footprint includes16 bytes of the next row.
  offset=self.destination-0x06000000
  if offset>=0xa000:offset-=0xa000
  image=bytearray(38400);coverage=bytearray(38400)
  image[offset:offset+len(self.indices)]=self.indices
  coverage[offset:offset+len(self.indices)]=bytes([1])*len(self.indices)
  return bytes(image),bytes(coverage)
 def compatible(self,newer):
  if self.epoch!=newer.epoch or self.refresh>=newer.refresh:raise ValueError('Unordered sky boundaries')
  if (self.asset_origin,self.width,self.height,self.center)!=(newer.asset_origin,newer.width,newer.height,newer.center):raise ValueError('Sky asset transition requires explicit handling')
  return True

@dataclass(frozen=True)
class SceneSky:
 boundary:SkyBoundary
 serial:int
 begin:int
 end:int
 asset:SkyAsset|None=None
 def __post_init__(self):
  if not 0<self.serial<2**32 or not 0<=self.begin<=self.boundary.refresh<=self.end<2**32-1:raise ValueError('Sky outside native scene interval')
  if self.asset is not None:self.asset.verify(self.boundary)
 def match_graph(self,graph):
  if graph.epoch!=self.boundary.epoch or graph.refresh!=self.end+1 or not self.begin<=graph.graph.refresh<=self.boundary.refresh:raise ValueError('Unpaired native sky scene')
  return self
