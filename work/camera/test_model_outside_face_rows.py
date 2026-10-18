import ctypes as C,struct
from pathlib import Path
lib=C.CDLL('work/camera/visibility-probe-wide.dll')
lib.nfs_model_face_visible.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
lib.nfs_model_face_rows.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);rect=(C.c_int32*4)(0,0,240,160);uv=struct.pack('<6H',0,0,1,0,0,1);indices=(C.c_uint16*3)(0,1,2)
for name,xy,expected in [('outside',[-30,10,-20,10,-20,20],1),('partial',[-10,10,10,10,10,20],0)]:
 points=struct.pack('<6h',*xy);visible=C.c_int();assert lib.nfs_model_face_visible(points,3,indices,3,C.byref(visible))
 if not visible.value:indices=(C.c_uint16*3)(2,1,0)
 out=(C.c_uint32*6000)(*([0x12345678]*6000));count=C.c_uint(77)
 ok=lib.nfs_model_face_rows(points,3,uv,3,indices,indices,3,rect,7,128,0x06000000,table,out,0 if name=='partial' else 1000,C.byref(count))
 assert ok==expected,(name,ok)
 assert count.value==(0 if expected else 77)
 assert all(x==0x12345678 for x in out)
count=C.c_uint();assert lib.nfs_model_face_rows(points,3,uv,3,indices,indices,3,rect,7,128,0x06000000,table,out,1000,C.byref(count)) and count.value>0
print('PASS outside rejection, clipped visible rows, atomic insufficient-capacity rejection')

