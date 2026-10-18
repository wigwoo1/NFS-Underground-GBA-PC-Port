from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'native_surface.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_wall_visibility_flag.argtypes=[Read,C.c_void_p,C.c_void_p,C.c_void_p,C.POINTER(C.c_int)]
state=bytearray(256);source=bytearray(68);mat=bytearray(32);struct.pack_into('<I',state,24,0x1000);fail=False;checks=0
@Read
def read(ctx,address,out,size):
 if fail or address!=0x1060 or size!=32:return 0
 C.memmove(out,bytes(mat),32);return 1
for override in (65535,3):
 for original in (0,1):
  for replacement in (0,1):
   struct.pack_into('<H',source,42,override);struct.pack_into('<H',source,46,original);struct.pack_into('<H',mat,14,replacement)
   out=C.c_int(123);assert d.nf_wall_visibility_flag(read,None,bytes(state),bytes(source),C.byref(out));assert out.value==int(not(original if override==65535 else replacement));checks+=1
fail=True;out=C.c_int(123);assert not d.nf_wall_visibility_flag(read,None,bytes(state),bytes(source),C.byref(out)) and out.value==123;checks+=1
report=dict(result='PASS',checks=checks,scope='Hidden source versus override precedence and atomic missing-read failure; not frustum/occlusion.')
(p/'wall-visibility-flag-tests.json').write_text(json.dumps(report,indent=2));print(report)
