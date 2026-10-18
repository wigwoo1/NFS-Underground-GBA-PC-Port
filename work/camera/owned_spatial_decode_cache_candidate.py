"""Thread-private bounded decode reuse; every caller retains a private rows dict."""
import threading
from types import MappingProxyType
from owned_spatial_descriptors import SpatialDescriptors
_original=SpatialDescriptors.__init__
_local=threading.local()

def cached_init(self,graph):
 geometry,offsets=graph.geometry,graph.offsets
 if type(geometry) is not bytes or type(offsets) is not bytes:return _original(self,graph)
 entries=getattr(_local,'entries',None)
 if entries is None:entries=[];_local.entries=entries
 for index,(g,o,rows) in enumerate(entries):
  if g is geometry and o is offsets:
   entries.append(entries.pop(index));self.rows=dict(rows);return
 _original(self,graph)
 entries.append((geometry,offsets,MappingProxyType(dict(self.rows))))
 if len(entries)>4:entries.pop(0)

def install():SpatialDescriptors.__init__=cached_init
