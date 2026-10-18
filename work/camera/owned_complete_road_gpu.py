"""GPU raw-road encoding; source owned fields only, no synthetic draw capture."""
import math,struct

def validate_road_record(context,candidate,bounds):
 if candidate.missing:raise ValueError('Incomplete road assets')
 if len(bounds)!=4 or not all(math.isfinite(x) for x in bounds) or not (0<=bounds[0]<=bounds[1]<=239 and 0<=bounds[2]<=bounds[3]<=159):raise ValueError('Invalid road clip bounds')
 if len(candidate.vertices)%68 or len(candidate.face)!=20 or len(candidate.material)!=32 or len(candidate.animation)!=8:raise ValueError('Incomplete road source record')
 count=len(candidate.vertices)//68
 if not 3<=count<=32 or len(candidate.offsets)!=count*32:raise ValueError('Invalid raw road ring')
 shift=struct.unpack_from('<H',candidate.material,26)[0];height=struct.unpack_from('<H',candidate.material,10)[0]
 if shift>10 or not height or len(candidate.texture)!=(1<<shift)*height*2:raise ValueError('Incomplete road texture')
 return count,shift,height

def encode_road(context,candidate,bounds):
 if candidate.missing:raise ValueError('Incomplete road assets')
 if len(bounds)!=4 or not all(math.isfinite(x) for x in bounds) or not (0<=bounds[0]<=bounds[1]<=239 and 0<=bounds[2]<=bounds[3]<=159):raise ValueError('Invalid road clip bounds')
 if len(candidate.vertices)%68 or len(candidate.face)!=20 or len(candidate.material)!=32 or len(candidate.animation)!=8:raise ValueError('Incomplete road source record')
 count=len(candidate.vertices)//68
 if not 3<=count<=32 or len(candidate.offsets)!=count*32:raise ValueError('Invalid raw road ring')
 # GPU consumes only count, UV offsets, shift/height and raw sources.
 # Other original runtime-scratch fields are deliberately zero, not reconstructed.
 material=bytearray(48);shift=struct.unpack_from('<H',candidate.material,26)[0];height=struct.unpack_from('<H',candidate.material,10)[0];struct.pack_into('<HH',material,36,shift,height)
 if shift>10 or not height or len(candidate.texture)!=(1<<shift)*height*2:raise ValueError('Incomplete road texture')
 du,dv=struct.unpack_from('<hh',candidate.animation,4);config=struct.pack('<8I',count,0,0,0,0,0,du&0xffffffff,dv&0xffffffff)
 envelope=tuple(int(x) for x in bounds) if all(int(x)==x for x in bounds) else (0,239,0,159)
 blocks=(candidate.vertices,candidate.offsets,candidate.face,bytes(material),context[256:304],struct.pack('<4H',*envelope),config,candidate.texture,context[384:896],candidate.descriptor_bytes,candidate.animation.ljust(64,b'\0'),context[304:368])
 return struct.pack('<4I',0x3147534e,1,0,12)+b''.join(struct.pack('<I',len(b))+b for b in blocks)
