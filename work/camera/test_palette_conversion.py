from pathlib import Path
import ctypes as C,struct,json
root=Path('work/camera');dll=C.CDLL(str((root/'visibility-probe-wide.dll').resolve()));R=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
f=dll.nf_extract_billboard;f.argtypes=[R,C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)];dll.nf_surface_free.argtypes=[C.c_void_p]
ctx=bytearray(44);struct.pack_into('<I',ctx,12,0x2000);struct.pack_into('<4I',ctx,16,0,0,8,4);struct.pack_into('<HHI',ctx,36,3,4,0x4000)
rect=struct.pack('<4i',-3,20,80,90);bounds=struct.pack('<4H',0,240,0,160);palette=b''.join(struct.pack('<H',i*113&32767) for i in range(256));indices=bytes([0,1,2,255]*8)
blocks={0x1000:bytes(ctx),0x2000:rect,0x30e2:bounds,0x05000000:palette,0x4000:indices};reject=None
@R
def read(user,address,out,size):
 if address==reject or address not in blocks or len(blocks[address])<size:return 0
 C.memmove(out,blocks[address],size);return 1
out=C.c_void_p();size=C.c_size_t();assert f(read,None,0x1000,0x3000,C.byref(out),C.byref(size));saved=C.string_at(out,size.value)
assert saved[:16]==struct.pack('<4I',0x3142464e,8,4,0) and saved[16:32]==rect and saved[32:48]==ctx[16:32] and saved[48:56]==bounds
for i,index in enumerate(indices):
 color=struct.unpack_from('<H',palette,index*2)[0];expected=bytes([(color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31,255 if index else 0]);assert saved[56+i*4:60+i*4]==expected
for reject in blocks:
 failed=C.c_void_p(1234);n=C.c_size_t(5678);assert not f(read,None,0x1000,0x3000,C.byref(failed),C.byref(n)) and failed.value==1234 and n.value==5678
reject=None
blocks.clear();assert C.string_at(out,size.value)==saved;dll.nf_surface_free(out)
struct.pack_into('<HHI',ctx,36,8,1,0x4000)
indices=bytes(range(256));tested=0
for base in range(0,65536,256):
 palette=b''.join(struct.pack('<H',base+i) for i in range(256))
 blocks.update({0x1000:bytes(ctx),0x2000:rect,0x30e2:bounds,0x05000000:palette,0x4000:indices})
 assert f(read,None,0x1000,0x3000,C.byref(out),C.byref(size))
 try:
  data=C.string_at(out,size.value)
  for index in indices:
   color=base+index
   expected=bytes([(color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31,255 if index else 0])
   assert data[56+index*4:60+index*4]==expected,(base,index);tested+=1
 finally:dll.nf_surface_free(out)
report=dict(result='PASS',palette_words=tested,all_16bit_palette_words=True,failed_read_atomic_cases=5,owned_after_source_removal=True,scope='Actual new extraction lookup path matches independent original channel arithmetic for all65536BGR555words including ignored high bit and indexed-zero alpha. Synthetic extraction, not live timing or fullscene gameplay proof.')
(root/'palette-conversion-tests.json').write_text(json.dumps(report,indent=2));print(report)
