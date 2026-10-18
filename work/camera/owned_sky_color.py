"""Reference per-scanline palette conversion for original fractional sky samples."""
import struct
import math
def sky_rgba(samples,palettes):
 palettes=bytes(palettes)
 if len(palettes)!=160*512 or len(samples.lower)!=15136 or len(samples.upper)!=15136 or not math.isfinite(samples.weight) or not 0<=samples.weight<1:raise ValueError('Incomplete sky color inputs')
 offset=(samples.destination-0x06000000)%0xa000
 if offset!=10560:raise ValueError('Unsupported sky placement')
 out=bytearray(15136*4)
 for row in range(64):
  begin=row*240;end=min(begin+240,15136)
  if begin>=end:break
  palette=struct.unpack_from('<256H',palettes,(44+row)*512)
  colors=[tuple(((c>>shift)&31)*8+(((c>>shift)&31)>>2) for shift in (0,5,10)) for c in palette]
  for i in range(begin,end):
   a=colors[samples.lower[i]];b=colors[samples.upper[i]]
   for k in range(3):out[i*4+k]=math.floor(a[k]+(b[k]-a[k])*samples.weight+.5)
   out[i*4+3]=255
 return bytes(out)
