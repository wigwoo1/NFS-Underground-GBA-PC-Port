"""Original integer scenery matrix builder from owned source/camera and ROM sine."""
import struct

def signed(value):
 value &= 0xffffffff
 return value-0x100000000 if value&0x80000000 else value

def multiply(a,b):
 return tuple(signed(sum(a[r*3+k]*b[k*3+c] for k in range(3)))>>14 for r in range(3) for c in range(3))

class SceneryProjection:
 def __init__(self,rom):
  start=0x623700
  if len(rom)<start+16384:raise ValueError('Missing owned sine table')
  self.sine=struct.unpack_from('<8192h',rom,start)
 def matrix(self,camera,source,initial=None):
  if len(camera)!=48 or len(source)!=164 or (initial is not None and len(initial)!=48):raise ValueError('Invalid scenery matrix inputs')
  model=struct.unpack_from('<h',source,54)[0];flags=struct.unpack_from('<H',source,10)[0]
  if not 30<=model<=36 or flags&32:raise ValueError('Unsupported scenery rotation source')
  cam=struct.unpack('<12i',camera);px,py,pz=struct.unpack_from('<3i',source,12)
  x=signed((px>>8)+cam[9]);z=signed((pz>>8)+cam[11]);depth=signed(cam[2]*x+cam[8]*z)>>14
  if not flags&2 and depth>3500:
   if initial is None:raise ValueError('Skipped builder requires owned initial matrix')
   return bytes(initial)
  def sine(angle):
   phase=angle&16383;value=self.sine[phase&8191]
   return -value if phase>=8192 else value
  ax,ay=struct.unpack_from('<2h',source,48);sx,cx,sy,cy=sine(ax),sine(ax+4096),sine(ay),sine(ay+4096)
  rx=(16384,0,0,0,cx,sx,0,-sx,cx);ry=(cy,0,-sy,0,16384,0,sy,0,cy)
  rotation=multiply(multiply(rx,cam[:9]),ry)
  translation=(signed(cam[0]*x+cam[6]*z)>>14,signed((py>>8)+cam[10]),depth)
  return struct.pack('<12i',*(rotation+translation))
