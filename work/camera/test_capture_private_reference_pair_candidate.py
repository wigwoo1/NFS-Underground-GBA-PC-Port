"""Actual private/transactional frame parity plus invalid admission checks."""
import ctypes as C,runpy,json
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
original=extension.capture
library=C.CDLL(str(Path('work/camera/viewport-sky-private-capture-probe.dll').resolve()))
f=library.nf_native_owned_frame_read;private=library.nf_native_owned_frame_read_private
for function in (f,private):function.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];function.restype=C.c_int
count=0;verified=0;frames=[]
reference_folder=Path("work/camera/prototype-runs/private-reference-pair-20261009");reference_folder.mkdir(exist_ok=True)
def capture(address,epoch,refresh):
 global count,verified
 packet=original(address,epoch,refresh);count+=1
 if count<=20 or refresh in (8873,8876):
  size=C.c_size_t();assert f(epoch,refresh,None,0,C.byref(size))==1 and size.value==len(packet)
  reference=C.create_string_buffer(size.value);assert f(epoch,refresh,reference,len(reference),C.byref(size))==1
  assert reference.raw==packet and type(packet) is bytes
  if refresh in (8873,8876):(reference_folder/(str(refresh)+".transactional.frame.bin")).write_bytes(reference.raw)
  sentinel=C.create_string_buffer(b'X'*16);written=C.c_size_t(123)
  assert private(epoch,refresh,sentinel,16,C.byref(written))==0 and sentinel.raw==b'X'*16+b'\0' and written.value==123
  assert private(epoch+1,refresh,sentinel,16,C.byref(written))==0 and written.value==123
  assert private(epoch,refresh+1000,sentinel,16,C.byref(written))==0 and written.value==123
  if len(frames)<2:frames.append(packet)
  verified+=1
 return packet
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_async_private_capture_candidate.py',run_name='__main__')
 assert verified>=20 and all(type(x) is bytes for x in frames)
 out=dict(result='PASS_ACTUAL_PRIVATE_FRAME_TRANSACTIONAL_PARITY',verified_frames=verified,captures=count,retained_frames_immutable=True,scope='Actual first20 private frame bytes equal original transactional reader; wrongepoch/refresh/capacity reject. Diagnostic doubles reads, no speed qualification.')
 Path('work/camera/prototype-runs/private-frame-captured-pair-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:extension.capture=original
