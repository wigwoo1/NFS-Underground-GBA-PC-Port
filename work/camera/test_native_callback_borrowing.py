"""Borrowed native function addresses must not grow ctypes ownership graphs."""
import ctypes as C,gc,weakref,json
from pathlib import Path
from live_native_batch_candidate import callback_address,Callback
lib=C.CDLL(str(Path(__file__).with_name('owned-batch-queued-candidate.dll').resolve()))
fn=lib.nf_owned_batch_sample_size
fn.restype=C.c_size_t
Expected=C.CFUNCTYPE(C.c_size_t)
original=dict(fn._objects or {})
enabled=gc.isenabled();gc.disable()
try:
 for _ in range(1000):
  wrapper=Expected(callback_address(fn))
  assert wrapper()==56
  ref=weakref.ref(wrapper);del wrapper
  assert ref() is None
  assert dict(fn._objects or {})==original
 cb=Callback(lambda p:17)
 before=dict(cb._objects or {})
 for _ in range(1000):
  wrapper=Callback(callback_address(cb));assert wrapper(None)==17
  ref=weakref.ref(wrapper);del wrapper;assert ref() is None
  assert dict(cb._objects or {})==before
finally:
 if enabled:gc.enable()
print('PASS 2000 borrowed native/Python callback calls, immediate wrapper release, unchanged ownership graphs')
