import ctypes as C,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()))
f=d.nf_owned_pose_face_visible;f.argtypes=[C.POINTER(C.c_double),C.c_uint,C.c_double,C.c_double,C.c_double,C.POINTER(C.c_int32)]
r=(C.c_int32*4)(0,0,240,160)
def check(vertices,expected):
 a=(C.c_double*(len(vertices)*5))(*[v for x,y,z in vertices for v in (x,y,z,0,0)])
 assert f(a,len(vertices),128,120,87,r)==expected
check([(-20,-20,128),(-20,20,128),(20,20,128),(20,-20,128)],1)
check([(-20,-20,128),(20,-20,128),(20,20,128),(-20,20,128)],0)
check([(-500,-500,128),(-500,500,128),(500,500,128),(500,-500,128)],1)
check([(500,-20,128),(500,20,128),(600,20,128),(600,-20,128)],0)
check([(-20,-20,63),(-20,20,128),(20,-20,128)],-1)
result=dict(result='PASS_CONTINUOUS_MODEL_VISIBILITY',cases=5,scope='Sampled camera-space winding and conservative viewport rejection; source scissor and scene membership remain unresolved.')
(p/'owned-pose-visibility-tests.json').write_text(json.dumps(result,indent=2));print(result)
