from pathlib import Path
import ctypes as C,json
p=Path('work/camera')
a=C.CDLL(str((p/'native_sprite.dll').resolve())).nfs_palette_rgb
b=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_palette_rgb
for f in (a,b):f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
src=(C.c_uint16*65536)(*range(65536));x=(C.c_uint32*65536)();y=(C.c_uint32*65536)()
assert a(src,65536,x) and b(src,65536,y) and bytes(x)==bytes(y)
print('PASS_EXHAUSTIVE_ORIGINAL_PALETTE_RGB')
