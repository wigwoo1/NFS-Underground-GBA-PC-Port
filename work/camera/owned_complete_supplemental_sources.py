"""Close supplemental wall assets using ROM geometry and paired captured materials."""
import struct
from owned_scene_bundle import chunks
from owned_supplemental_rom_geometry import recover_geometry
from owned_graph_wall_sources import WallSource

def _complete_wall_sources(closed,supplements,rom):
 if (closed.epoch,closed.refresh,closed.graph.refresh)!=(supplements.epoch,supplements.refresh,supplements.source_refresh):raise ValueError('Unpaired supplemental asset closure')
 assets=recover_geometry(closed,rom);materials={}
 for _,raw in chunks(supplements.textures,'textures'):
  h=struct.unpack_from('<12I',raw)
  value=(bytes(raw[48:120]),bytes(raw[120:]),h[7],h[8],h[9])
  if h[5] in materials and materials[h[5]]!=value:raise ValueError('Supplemental material changed within scene')
  materials[h[5]]=value
 out=[]
 for asset in assets.values():
  count=len(asset.ring)//68
  if any(i!=65535 for i in asset.offset_indices):raise ValueError('Uncaptured supplemental offset dependency')
  for edge,mi in enumerate(asset.material_indices):
   if mi==65535:continue
   if mi not in materials:raise ValueError('Missing complete supplemental material')
   raw,texture,shift,height,address=materials[mi]
   if len(texture)!=(1<<shift)*height:raise ValueError('Incomplete supplemental texture')
   if not height:continue
   nxt=(edge+1)%count
   out.append(WallSource(asset.descriptor,edge,asset.ring[edge*68:(edge+1)*68]+asset.ring[nxt*68:(nxt+1)*68],bytes(64),raw[32:40],raw[40:72],texture,shift,height,address))
 return tuple(out)

import threading
_supplemental_cache_local=threading.local()
def complete_wall_sources(closed,supplements,rom):
 if (closed.epoch,closed.refresh,closed.graph.refresh)!=(supplements.epoch,supplements.refresh,supplements.source_refresh):raise ValueError('Unpaired supplemental asset closure')
 entries=getattr(_supplemental_cache_local,'entries',[])
 for graph,packet,source,assets in entries:
  if graph is closed and packet is supplements and source is rom:return assets
 assets=_complete_wall_sources(closed,supplements,rom)
 entries.append((closed,supplements,rom,assets));_supplemental_cache_local.entries=entries[-4:]
 return assets
