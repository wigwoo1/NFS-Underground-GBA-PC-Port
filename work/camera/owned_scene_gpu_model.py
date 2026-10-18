"""Adapt verified owned scene model draws to native GPU geometry blocks."""
import struct
from owned_graph_packet import GraphPacket
from owned_scene_bundle import chunks

def blocks(bundle,meshed,model_palette):
 model_palette=bytes(model_palette)
 if len(model_palette)!=512:raise ValueError('Missing draw-time model palette')
 graph=GraphPacket.decode(bundle.graph);draw=meshed.draw;mesh=meshed.mesh
 region=next((raw[32:48] for h,raw in chunks(bundle.associations,'associations') if h[7]==draw.region),None)
 if region is None:raise ValueError('Missing model clip region')
 _,left,right,top,bottom,flags,depth,tail=struct.unpack('<8H',region)
 context=bytearray(68);context[56:60]=draw.material[26:28]+draw.material[10:12]
 framebuffer=graph.context[304:368];context[64:68]=framebuffer[28:32]
 descriptor,vertices,faces,vi,ui,uv=mesh.blocks
 return (bytes(context),descriptor,draw.matrix,framebuffer,vertices,faces,vi,ui,uv,struct.pack('<4i',left,top,right,bottom),draw.texture,model_palette)

def encode(bundle,meshed,model_palette):
 owned=blocks(bundle,meshed,model_palette)
 return struct.pack('<4I',0x3147534e,3,0,12)+b''.join(struct.pack('<I',len(b))+b for b in owned)

def palette(bundle,meshed,encoded):
 from owned_scene_model_binding import identity
 raw=bytes(encoded)
 if len(raw)%756:raise ValueError('Truncated draw palette')
 camera=GraphPacket.decode(bundle.graph).context[256:304];matches=[]
 for offset in range(0,len(raw),756):
  h=struct.unpack_from('<8I',raw,offset)
  if h[0]!=0x314c504e or h[6]!=724 or h[7]!=1:raise ValueError('Invalid draw palette')
  if raw[offset+196:offset+244]==camera and identity(raw[offset+32:offset+196])==identity(meshed.draw.source):matches.append(raw[offset+244:offset+756])
 if len(matches)!=1:raise ValueError('Missing or duplicate model draw palette')
 return matches[0]
