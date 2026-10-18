"""Read only exact completed native scene sky identity into immutable storage."""
import ctypes as C
from functools import lru_cache
SkyIdentity=C.c_uint32*3
@lru_cache(maxsize=8)
def sky_copy_type(size):return C.c_char*size
from owned_sky_boundary import SkyBoundary,SceneSky
from owned_sky_sampler import SkyAsset
class SkyCapture:
 def __init__(self,d,rom=None):
  self.d=d;self.serial=0;self.records=[];self.rom=bytes(rom) if rom is not None else None;self.assets={}
  d.nf_live_completed_sky_publication_identity.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
  d.nf_live_completed_sky_read.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 def read(self,graph):
  ident=SkyIdentity()
  if not self.d.nf_live_completed_sky_publication_identity(graph.epoch,graph.refresh,ident):
   api=self.d.nf_live_sky_history_diagnostic;api.argtypes=[C.c_void_p,C.c_uint];snapshot=(C.c_uint32*132)();assert api(snapshot,132)
   scene_stats=(C.c_uint32*4)()
   self.d.nf_native_scene_stats.argtypes=[C.POINTER(C.c_uint32)]
   self.d.nf_native_scene_stats(scene_stats)
   self.d.nf_native_scene_refresh.restype=C.c_uint
   self.d.nf_native_scene_epoch.restype=C.c_uint64
   native_refresh=int(self.d.nf_native_scene_refresh())
   native_epoch=int(self.d.nf_native_scene_epoch())
   raise ValueError(f'Missing or ambiguous exact native sky scene identity epoch={graph.epoch} publication={graph.refresh} source={graph.graph.refresh} history={list(snapshot)} live_scene_stats={list(scene_stats)} native_epoch={native_epoch} native_refresh={native_refresh}')
  serial,begin,end=ident;n=C.c_size_t()
  if not self.d.nf_live_completed_sky_read(graph.epoch,serial,0,None,0,C.byref(n)):raise ValueError('Missing owned sky copy')
  buf=sky_copy_type(n.value)()
  if not self.d.nf_live_completed_sky_read(graph.epoch,serial,0,buf,n.value,C.byref(n)):raise ValueError('Sky ownership expired')
  boundary=SkyBoundary.decode(buf.raw)
  asset=None
  if self.rom is not None:
   key=(boundary.epoch,boundary.asset_origin)
   if key not in self.assets:
    self.assets={k:v for k,v in self.assets.items() if k[0]==boundary.epoch}
    offset=boundary.asset_origin-0x08000000
    self.assets[key]=SkyAsset(boundary.asset_origin,self.rom[offset:offset+15376])
   asset=self.assets[key];asset.verify(boundary)
  result=SceneSky(boundary,serial,begin,end,asset).match_graph(graph);self.serial=serial;self.records.append(dict(epoch=graph.epoch,publication=graph.refresh,serial=serial,begin=begin,end=end,copy_refresh=result.boundary.refresh,angle=boundary.angle,source=boundary.source,asset_origin=boundary.asset_origin));return result
