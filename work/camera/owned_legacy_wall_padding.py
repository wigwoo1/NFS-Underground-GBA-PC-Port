"""Diagnostic-only legacy padding expansion; no sampled source bytes ignored."""
import struct
from owned_motion_pairs import records
def legacy_wall_padding(sample):
 frame,*tail=sample;header=list(struct.unpack_from('<6I2Q',frame));out=[]
 for row in records(frame)['records']:
  blocks=list(row['blocks'])
  if row['kind']==2 and len(blocks[8])!=65536:
   shift,height=struct.unpack_from('<HH',blocks[4],36)
   if shift>10 or not 0<height<=1024 or len(blocks[8])!=(1<<shift)*height or len(blocks[8])>65536:raise ValueError('Invalid compact wall footprint')
   blocks[8]=bytes(blocks[8]).ljust(65536,b'\x00')
  out.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+bytes(x) for x in blocks))
 geometry=b''.join(out);end=frame[40+header[2]:];header[2]=len(geometry)
 return (struct.pack('<6I2Q',*header)+geometry+end,*tail)
