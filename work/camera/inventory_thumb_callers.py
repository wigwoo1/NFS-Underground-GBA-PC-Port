"""Recover aligned Thumb BL references directly from immutable ROM bytes."""
def callers(rom,target,base=0x08000000,limit=0x78000):
 result=[]
 for off in range(0,min(len(rom),limit)-3,2):
  a=int.from_bytes(rom[off:off+2],'little');b=int.from_bytes(rom[off+2:off+4],'little')
  if a&0xf800!=0xf000 or b&0xf800!=0xf800:continue
  delta=((a&0x7ff)<<12)|((b&0x7ff)<<1)
  if delta&(1<<22):delta-=1<<23
  if base+off+4+delta==target:result.append(base+off)
 return result
