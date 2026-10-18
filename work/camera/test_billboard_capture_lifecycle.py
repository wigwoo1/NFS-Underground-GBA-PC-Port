from pathlib import Path
import ctypes as C,struct,json
root=Path('work').resolve();d=C.CDLL(str(root/'camera/visibility-probe.dll'));rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
R=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_billboard_capture_reader.argtypes=[R,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32];d.nf_live_billboard_copy.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)];d.nf_live_billboard_identity.argtypes=[C.POINTER(C.c_uint64),C.c_void_p];d.nf_surface_free.argtypes=[C.c_void_p]
@Sink
def receive(a,b,c,e):return 1
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(receive,None);d.nf_live_surface_audit_enable(1)
 for frame in range(20):d.nf_frame(1)
 ctx=bytearray(44);struct.pack_into('<I',ctx,12,0x2000);struct.pack_into('<4I',ctx,16,0,0,8,4);struct.pack_into('<HHI',ctx,36,3,4,0x4000)
 blocks={0x1000:bytes(ctx),0x2000:struct.pack('<4I',0,0,8,4),0x30e2:struct.pack('<4H',0,240,0,160),0x05000000:bytes(512),0x4000:bytes([1]*32)}
 @R
 def read(user,address,out,size):
  if address not in blocks or size>len(blocks[address]):return 0
  C.memmove(out,blocks[address],size);return 1
 def capture():assert d.nf_live_billboard_capture_reader(read,None,0x1000,0x3000,0x4444)
 def copy(epoch,serial,success):
  ptr=C.c_void_p(1234);size=C.c_size_t(5678);ok=d.nf_live_billboard_copy(epoch,serial,C.byref(ptr),C.byref(size));assert bool(ok)==success
  if not success:assert ptr.value==1234 and size.value==5678;return
  data=C.string_at(ptr,size.value);return ptr,size.value,data
 capture();epoch=C.c_uint64();identity=(C.c_uint32*3)();assert d.nf_live_billboard_identity(C.byref(epoch),identity);assert identity[2]==0x4444
 first=copy(epoch.value,identity[0],True);copy(epoch.value+1,identity[0],False);copy(epoch.value,identity[0]+1,False)
 blocks[0x4000]=bytes(32);capture();second=copy(epoch.value,identity[0],True);assert first[2]!=second[2] and C.string_at(first[0],first[1])==first[2]
 del blocks[0x4000];assert not d.nf_live_billboard_capture_reader(read,None,0x1000,0x3000,0x4444);copy(epoch.value,identity[0],False)
 blocks[0x4000]=bytes(32);capture();d.nf_native_scene_discontinuity();copy(epoch.value,identity[0],False)
 for ptr,size,data in [first,second]:assert C.string_at(ptr,size)==data;d.nf_surface_free(ptr)
 report=dict(result='PASS',fixture_captures=3,failed_capture_clears=True,wrong_identity_atomic=True,replacement_and_reset_preserve_caller_copy=True,scope='Synthetic reader injected through shared research capture path; not an observed CPU2578 event.')
 (root/'camera/billboard-capture-lifecycle-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:d.nf_close()
