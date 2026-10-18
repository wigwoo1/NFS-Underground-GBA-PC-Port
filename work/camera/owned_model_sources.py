"""Immutable known-model source bytes paired to original graph capture time."""
import struct
from dataclasses import dataclass
from types import MappingProxyType
@dataclass(frozen=True)
class OwnedModelSources:
 epoch:int
 refresh:int
 source_refresh:int
 sources:object
 removals:object
 payload:bytes
 external:object=None
 @classmethod
 def decode(cls,payload,graph):
  raw=bytes(payload)
  if len(raw)<32:raise ValueError('Truncated model source packet')
  magic,version,refresh,source,count,stride,epoch=struct.unpack_from('<6IQ',raw)
  if magic!=0x31534f4e or (version,stride) not in ((2,168),(3,176),(4,216)) or count>1024 or len(raw)!=32+count*stride:raise ValueError('Invalid model source packet')
  if (epoch,refresh,source)!=(graph.epoch,graph.refresh,graph.graph.refresh):raise ValueError('Unpaired model source clock')
  sources={};removals={};external={}
  for i in range(count):
   address=struct.unpack_from('<I',raw,32+i*stride)[0]
   if address in sources:raise ValueError('Repeated model source identity')
   sources[address]=raw[36+i*stride:200+i*stride]
   if version>=3:
    time,pc=struct.unpack_from('<2I',raw,200+i*stride)
    if (time==0)!=(pc==0) or time>source or pc not in (0,0x0801e4c2):raise ValueError('Invalid source removal event')
    if time:removals[address]=(time,pc)
   if version==4 and struct.unpack_from('<H',sources[address],10)[0]&32:
    enabled=struct.unpack_from('<I',raw,208+i*stride)[0]
    external[address]=(enabled,raw[212+i*stride:248+i*stride])
  return cls(epoch,refresh,source,MappingProxyType(sources),MappingProxyType(removals),raw,MappingProxyType(external))

