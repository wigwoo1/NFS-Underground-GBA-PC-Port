"""Original sky horizontal source phase; recovered from ROM08004bdc..4bf6."""
def source_offset(angle,width,center):
 if not 1<=width<=65535:raise ValueError('Invalid sky width')
 if not -32768<=center<=32767:raise ValueError('Invalid signed center')
 scaled=(((angle&0x3fff)*width)<<2)&0xffffffff
 if scaled&0x80000000:scaled-=1<<32
 dividend=scaled>>14
 phase=(abs(dividend)%width)*(-1 if dividend<0 else 1)
 return (phase-center)&~1
