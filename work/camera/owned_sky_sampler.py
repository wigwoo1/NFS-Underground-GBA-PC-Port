"""Fractional owned sky source sampling for the integrated queued GPU renderer."""
from dataclasses import dataclass
import math
from owned_sky_scroll import source_offset
@dataclass(frozen=True)
class SkySamples:
 lower:bytes
 upper:bytes
 weight:float
 destination:int
@dataclass(frozen=True)
class SkyAsset:
 origin:int
 data:bytes
 def __post_init__(self):
  object.__setattr__(self,'data',bytes(self.data))
  if len(self.data)!=15376:raise ValueError('Incomplete sky source span')
 def verify(self,b):
  offset=b.source-self.origin
  if self.origin!=b.asset_origin or b.center!=0 or not 0<=offset<=238 or self.data[offset:offset+15136]!=b.indices:raise ValueError('Sky asset endpoint mismatch')
 def sample(self,a,b,alpha):
  a.compatible(b);self.verify(a);self.verify(b)
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid interpolation fraction')
  # Original angle is14bits; phase makes four turns per angle revolution.
  delta=((b.angle-a.angle+8192)&16383)-8192
  expected=delta*240/4096
  if abs(expected)>=120:raise ValueError('Ambiguous sky motion interval')
  lo=source_offset(a.angle,240,0);hi=source_offset(b.angle,240,0)
  travel=hi-lo+240*round((expected-(hi-lo))/240)
  phase=(lo+travel*alpha)%240
  # Snap both original endpoints to exact owned copies, including16byte tail.
  if alpha==0:return SkySamples(a.indices,a.indices,0,a.destination)
  if alpha==1:return SkySamples(b.indices,b.indices,0,b.destination)
  base=math.floor(phase);weight=phase-base
  upper=(base+1)%240
  return SkySamples(self.data[base:base+15136],self.data[upper:upper+15136],weight,a.destination)

 def sample_continuous(self,a,b,alpha):
  """Native subpixel phase from original angle, including continuous endpoints.

  Original byte-copy fidelity remains available through sample(). Keeping
  fractional phase at endpoints avoids snapping at each scene-pair boundary.
  """
  a.compatible(b);self.verify(a);self.verify(b)
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid interpolation fraction')
  delta=((b.angle-a.angle+8192)&16383)-8192
  if abs(delta*240/4096)>=120:raise ValueError('Ambiguous sky motion interval')
  angle=(b.angle&16383) if alpha==1 else (a.angle&16383)+delta*alpha
  phase=(angle*240/4096)%240
  base=math.floor(phase);weight=phase-base
  upper=(base+1)%240
  return SkySamples(self.data[base:base+15136],self.data[upper:upper+15136],weight,a.destination)
