"""Private-output partial failures never publish a Python frame."""
import ctypes as C,struct
from pathlib import Path
import _owned_frame_capture_profile_candidate as m
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
for mode in ('partial_failure','short_write','bad_epoch'):
 @Reader
 def callback(e,r,p,n,w):
  w[0]=len(raw)
  if not p:return 1
  if mode=='partial_failure':C.memmove(p,raw,40);return 0
  C.memmove(p,raw,len(raw))
  if mode=='short_write':w[0]-=1
  else:C.c_uint64.from_address(p+24).value+=1
  return 1
 try:m.capture(C.cast(callback,C.c_void_p).value,epoch,refresh)
 except ValueError:pass
 else:raise AssertionError(mode+' published')
print('PASS_PRIVATE_CAPTURE_PARTIAL_FAILURE_DISCARD')
