"""Native query-to-queue evaluation from one immutable memory snapshot."""
from pathlib import Path
import ctypes as C,json,struct,hashlib
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_evaluate
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);cases=failures=wrong_view=0
for name in json.loads((root/'pipeline-capture-manifest.json').read_text()):
 data=(root/'pipeline-corpus'/name).read_bytes();stride=88+0x48000
 headers=[struct.unpack_from('<22I',data,i*stride) for i in range(4)]
 snapshots=[data[i*stride+88:(i+1)*stride] for i in range(4)]
 def memory(stage,address,size):
  for base,chunk in [(0x02000000,snapshots[stage][:0x40000]),(0x03000000,snapshots[stage][0x40000:]),(0x08000000,rom)]:
   if base<=address and address+size<=base+len(chunk):return chunk[address-base:address-base+size]
  raise ValueError((hex(address),size))
 def word(stage,address):return struct.unpack('<I',memory(stage,address,4))[0]
 def half(stage,address):return struct.unpack('<H',memory(stage,address,2))[0]
 h=headers[0];stateaddr=h[4];sp=h[19];table=word(0,stateaddr+0x60);member=word(0,stateaddr+0x64)
 initial=[memory(0,stateaddr,256),b'\xcc'*16+memory(0,table+16,304),memory(0,member,4096)]
 expected=[memory(3,stateaddr,256),memory(3,table,320),memory(3,member,4096)]
 selected_initial=half(0,0x03005d44);recovery=half(0,word(0,sp+0xa4)+0x78)
 base=(C.c_uint32*2)(h[7],h[6])
 query=C.create_string_buffer(memory(0,word(0,sp+0x98),48))
 view=C.create_string_buffer(memory(2,word(2,stateaddr+0x54),48))
 source_hash=hashlib.sha256(snapshots[0]).hexdigest();reads=[];errors=[]
 @Reader
 def read(ctx,address,dest,size):
  try:reads.append((address,size));C.memmove(dest,memory(0,address,size),size);return 1
  except Exception as e:errors.append(str(e));return 0
 buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(selected_initial)
 assert fn(*buffers,C.byref(selected),recovery,base,query,view,read,None,reciprocal) and not errors
 assert [b.raw[:len(e)] for b,e in zip(buffers,expected)]==expected,name
 assert selected.value==half(3,0x03005d44)
 assert hashlib.sha256(snapshots[0]).hexdigest()==source_hash
 total_reads=len(reads)
 for index in range(total_reads):
  calls=[0]
  @Reader
  def fail(ctx,address,dest,size):
   calls[0]+=1
   if calls[0]==index+1:return 0
   C.memmove(dest,memory(0,address,size),size);return 1
  buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(selected_initial)
  assert not fn(*buffers,C.byref(selected),recovery,base,query,view,fail,None,reciprocal)
  assert selected.value==selected_initial
  assert [b.raw[:len(e)] for b,e in zip(buffers,initial)]==initial
  failures+=1
 # Negative control: serving the query matrix to the builder must be detectable.
 buffers=[C.create_string_buffer(b) for b in initial];selected=C.c_uint32(selected_initial)
 ok=fn(*buffers,C.byref(selected),recovery,base,query,query,read,None,reciprocal)
 wrong_view+=not ok or [b.raw[:len(e)] for b,e in zip(buffers,expected)]!=expected
 cases+=1
assert cases==24 and wrong_view>0
report=dict(result='PASS',single_snapshot_native_sequences=cases,atomic_read_failure_checks=failures,wrong_matrix_detected_cases=wrong_view,
 scope='All query/root/builder memory reads use query-entry snapshot; separate recorded view matrix is explicitly supplied. Exact original final state/queue/groups/selected match. Camera-input policy and live interpolation remain external.')
(root/'visibility-evaluate-tests.json').write_text(json.dumps(report,indent=2));print(report)
