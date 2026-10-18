from pathlib import Path
import ctypes as C,json,struct
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_build_pair
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
coverage=json.loads((root/'visibility-builder-coverage.json').read_text());cases=failures=0
for group in coverage['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();size=88+0x48000;h=struct.unpack_from('<22I',blob);ram=blob[88:size];post=blob[size+88:]
  def memory(addr,n,source=ram):
   for base,data in [(0x02000000,source[:0x40000]),(0x03000000,source[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+n<=base+len(data):return data[addr-base:addr-base+n]
   raise ValueError((hex(addr),n))
  state=memory(h[4],256);table,member=struct.unpack_from('<2I',state,0x60)
  chosen=struct.unpack('<H',memory(0x03005d44,2))[0]
  # Deliberately discard captured root; implementation must reconstruct it.
  initial=[state,b'\xcc'*16+memory(table+16,304),memory(member,4096)]
  expected=[memory(h[4],256,post),memory(table,320,post),memory(member,4096,post)]
  for pair in [(chosen,chosen),(65535,chosen),(chosen,65535),(chosen,(chosen+1)%512)]:
   errors=[];reads=[]
   @Reader
   def read(ctx,addr,dst,n):
    try:reads.append((addr,n));C.memmove(dst,memory(addr,n),n);return 1
    except Exception as e:errors.append(str(e));return 0
   buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(0xdddddddd);p=(C.c_uint32*2)(*pair)
   assert fn(*buffers,p,C.byref(selected),read,None,reciprocal) and not errors
   assert selected.value==chosen
   assert [b.raw[:len(e)] for b,e in zip(buffers,expected)]==expected,(sample['file'],pair)
   cases+=1
   # Every read, including failures after root selection, is transactional.
   if pair==(chosen,chosen):
    for index in range(len(reads)):
     calls=[0]
     @Reader
     def fail(ctx,addr,dst,n):
      calls[0]+=1
      if calls[0]==index+1:return 0
      C.memmove(dst,memory(addr,n),n);return 1
     buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(0xdddddddd)
     assert not fn(*buffers,p,C.byref(selected),fail,None,reciprocal)
     assert selected.value==0xdddddddd
     assert [b.raw[:len(e)] for b,e in zip(buffers,initial)]==initial
     failures+=1
buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(0xdddddddd)
assert not fn(*buffers,(C.c_uint32*2)(65535,65535),C.byref(selected),read,None,reciprocal)
assert selected.value==0xdddddddd and [b.raw[:len(e)] for b,e in zip(buffers,initial)]==initial
report=dict(result='PASS',captured_worlds=69,pair_variants_exact=cases,atomic_snapshot_read_failures=failures,absent_pair_atomic=True,
 scope='Native pair choice, root initialization and complete builder compared with captured final state/queue/groups. Pair variants are supplied fixtures; query-to-builder temporal coherence and intermediate poses remain unverified.')
(root/'visibility-build-pair-tests.json').write_text(json.dumps(report,indent=2));print(report)
