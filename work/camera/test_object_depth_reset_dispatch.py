"""Compare depth-reset model classification with the recovered native selector."""
import ctypes as C
import struct
from owned_object_dispatch import select
lib=C.CDLL('work/camera/visibility-probe-wide.dll')
u8=C.c_uint8;u32=C.c_uint32
lib.nfs_visibility_object_texture.argtypes=[C.POINTER(u8),C.POINTER(u8),C.POINTER(u8),u32,u32,C.POINTER(u32)]
state=bytearray(256);struct.pack_into('<I',state,124,0x08331624)
for flags,model,depth in ((2,35,5880),(2,0,5880),(0,7,306),(0,7,1500),(64,7,1500)):
 source=bytearray(164);struct.pack_into('<H',source,10,flags);struct.pack_into('<h',source,54,model)
 result=select(source,state,depth)
 material=(u8*32)();previous=(u8*32)();output=(u32*2)()
 assert lib.nfs_visibility_object_texture((u8*164).from_buffer_copy(source),material,previous,0,result['depth'],output)==1
 assert result['kind']==('billboard' if output[1] else 'model'),(flags,model,depth,result,list(output))
print('PASS five ordinary model/billboard branches agree with native texture selection')
