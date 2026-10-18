"""Project supplemental rings from complete assets without captured invocation geometry."""
import struct
from owned_supplemental_rom_geometry import recover_geometry
from owned_complete_supplemental_sources import complete_wall_sources
from owned_scene_bundle import chunks
from owned_wall_projection import projected
from owned_supplemental_palette import resolve_palette

def projection_input(closed,supplements,rom,descriptor,bounds,*,palette_required=True):
 if len(bounds)!=4 or any(int(x)!=x for x in bounds):raise ValueError('Endpoint projection requires integral owned bounds')
 if not 0<=bounds[0]<=bounds[1]<=239 or not 0<=bounds[2]<=bounds[3]<=159:raise ValueError('Invalid supplemental bounds')
 assets=recover_geometry(closed,rom)
 if descriptor not in assets:raise ValueError('Unowned supplemental descriptor')
 asset=assets[descriptor];sources=tuple(w for w in complete_wall_sources(closed,supplements,rom) if w.descriptor==descriptor)
 materials={}
 for _,raw in chunks(supplements.textures,'textures'):
  h=struct.unpack_from('<12I',raw);materials[h[5]]=raw[48:120]
 # Visibility-only callers explicitly omit raster palette ownership.
 palette=resolve_palette(closed,supplements,sources,descriptor,bounds) if palette_required else bytes(512)
 n=len(asset.ring)//68;state=closed.graph.context[:256]
 # This is a component projection input, never an original invocation record.
 header=struct.pack('<8I',0x3147534e,closed.graph.refresh,next(iter(chunks(closed.objects,'graph_objects')))[0][2],descriptor,n,944+n*140,1,0)
 payload=asset.raw_descriptor+closed.graph.context[256:304]+closed.graph.context[304:368]+struct.pack('<8H',descriptor,*map(int,bounds),0,0,65535)+state+palette
 for i in range(n):
  vertex=asset.ring[i*68:(i+1)*68];mi=asset.material_indices[i]
  material=bytes(72) if mi==65535 else materials[mi]
  payload+=vertex+bytes(32)+material[:32]+material[32:40]
 assert len(payload)==944+n*140
 return header+payload,sources

def project_complete(closed,supplements,rom,descriptor,bounds,reciprocal):
 return projected(closed.graph,reciprocal,projection_input(closed,supplements,rom,descriptor,bounds))




