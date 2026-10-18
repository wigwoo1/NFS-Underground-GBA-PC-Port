import ctypes as C,math
from pathlib import Path
lib=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()))
a=lib.nf_owned_pose_face_visible;a.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_double,C.c_void_p]
b=lib.nf_owned_pose_face_visible_fractional;b.argtypes=a.argtypes
points=(C.c_double*15)(40.25,20,64,0,0,40.25,30,64,0,0,42.75,20,64,0,0)
for rect in ((0,0,240,160),(43,0,240,160),(0,0,40,160),(40,20,43,31)):
 integer=(C.c_int32*4)(*rect);fractional=(C.c_double*4)(*rect)
 assert a(points,3,64,0,0,integer)==b(points,3,64,0,0,fractional)
assert b(points,3,64,0,0,(C.c_double*4)(42.7,0,240,160))==1
assert b(points,3,64,0,0,(C.c_double*4)(42.8,0,240,160))==0
assert b(points,3,64,0,0,(C.c_double*4)(float('nan'),0,240,160))==-1
print('PASS integer face compatibility, fractional42.7/42.8 clip boundary distinction and NaN rejection')
