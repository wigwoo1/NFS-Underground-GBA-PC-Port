from pathlib import Path
import ctypes as C, struct, json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'native_surface.dll'))
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
f=d.nf_wall_write_states_owned
f.argtypes=[Reader,C.c_void_p,C.c_uint32,C.c_uint,C.POINTER(C.c_void_p)]+[C.POINTER(C.c_uint32)]*3
d.nf_surface_free.argtypes=[C.c_void_p]
material=bytearray(48);struct.pack_into('<I',material,8,0x2000)
struct.pack_into('<HHI',material,36,8,1,0x3000)
context=bytearray(24);struct.pack_into('<I',context,20,0x4000)
texture=bytes(range(256));table=bytes((i+level)%256 for i in range(256) for level in range(16))
regions={0x1000:material,0x2000:context,0x3000:texture,0x4000:table}
@Reader
def read(user,address,out,size):
    for base,data in regions.items():
        if base<=address and address+size<=base+len(data):
            C.memmove(out,bytes(data[address-base:address-base+size]),size);return 1
    return 0
checked=0
for flags,planes in ((0,17),(256,1)):
    ptr=C.c_void_p();w=C.c_uint32();h=C.c_uint32();n=C.c_uint32()
    assert f(read,None,0x1000,flags,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
    assert (w.value,h.value,n.value)==(256,1,planes)
    expected=bytes(2 if i else 0 for i in range(256))
    if planes==17:
        expected+=bytes(0 if not i else 2 if table[i*16+level] else 1 for level in range(16) for i in range(256))
    # Returned ownership survives reader data mutation.
    saved=regions.copy();regions.clear()
    assert C.string_at(ptr,len(expected))==expected
    regions.update(saved);d.nf_surface_free(ptr);checked+=len(expected)
rejects=0
for flags,missing in ((128,None),(0,0x3000),(0,0x4000),(0,0x2000),(256,0x1000)):
    saved=regions.pop(missing) if missing else None
    ptr=C.c_void_p(123);w=C.c_uint32(41);h=C.c_uint32(42);n=C.c_uint32(43)
    assert not f(read,None,0x1000,flags,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
    assert (ptr.value,w.value,h.value,n.value)==(123,41,42,43)
    if missing:regions[missing]=saved
    rejects+=1
for shift,height,address in ((11,1,0x3000),(8,0,0x3000),(8,1,0xffffff80)):
    saved=bytes(material);struct.pack_into('<HHI',material,36,shift,height,address)
    ptr=C.c_void_p(123);w=C.c_uint32(41);h=C.c_uint32(42);n=C.c_uint32(43)
    assert not f(read,None,0x1000,256,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
    assert (ptr.value,w.value,h.value,n.value)==(123,41,42,43)
    material[:]=saved;rejects+=1
report=dict(result='PASS',exact_classifications=checked,atomic_rejections=rejects,
            scope='Owned base and16lighting wall write-state planes with all256source indices and synthetic output-zero mappings; no command/packet/live integration yet')
(p/'wall-write-states-tests.json').write_text(json.dumps(report,indent=2));print(report)
