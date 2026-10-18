from pathlib import Path
import ctypes as C,json
root=Path('work/camera');d=C.CDLL(str((root/'draw-palette.dll').resolve()))
create=d.nf_draw_palettes_create;create.argtypes=[C.c_uint64,C.c_uint32];create.restype=C.c_void_p
append=d.nf_draw_palettes_append;append.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_size_t]
seal=d.nf_draw_palettes_seal;seal.argtypes=[C.c_void_p]
read=d.nf_draw_palettes_read;read.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_uint,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_size_t]
info=d.nf_draw_palettes_info;info.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
destroy=d.nf_draw_palettes_destroy;destroy.argtypes=[C.c_void_p]
def counts(p):
 n=C.c_uint();u=C.c_uint();b=C.c_size_t();assert info(p,C.byref(n),C.byref(u),C.byref(b));return n.value,u.value,b.value
assert not create(0,7)
p=create(1,7);assert p
palette=C.create_string_buffer(bytes(512));out=C.create_string_buffer(b'X'*512)
assert not read(p,1,7,0,1,10,20,out,512) and out.raw[:512]==b'X'*512
for i in range(64):
 data=bytes([i])*512;C.memmove(palette,data,512);assert append(p,1,10,20,palette,512)
assert counts(p)[:2]==(64,64)
C.memset(palette,200,512);before=counts(p);assert not append(p,1,10,20,palette,512) and counts(p)==before
for i in range(192):
 C.memset(palette,i%64,512);assert append(p,1,10,20,palette,512)
assert counts(p)[:2]==(256,64);assert not append(p,1,10,20,palette,512)
assert seal(p) and not seal(p) and not append(p,1,10,20,palette,512)
C.memset(palette,255,512)
for i in range(256):
 assert read(p,1,7,i,1,10,20,out,512) and out.raw[:512]==bytes([i%64])*512
invalid=0
for args in [(2,7,0,1,10,20),(1,8,0,1,10,20),(1,7,256,1,10,20),(1,7,0,2,10,20),(1,7,0,1,11,20),(1,7,0,1,10,21)]:
 C.memset(out,88,512);assert not read(p,*args,out,512) and out.raw[:512]==b'X'*512;invalid+=1
size=counts(p)[2];destroy(p)
report=dict(result='PASS',draws_verified=256,deduplicated_palettes=64,owned_bytes=size,identity_failures=invalid,source_overwrite_safe=True,capacity_failures_atomic=True,sealed_immutable=True,scope='Synthetic palette-bank ownership/identity/capacity tests; not yet live scene integration.')
(root/'draw-palette-tests.json').write_text(json.dumps(report,indent=2));print(report)
