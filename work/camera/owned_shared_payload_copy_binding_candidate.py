"""Synchronous native copy with strong immutable bytes and shared mapping owners."""
import ctypes as C
from pathlib import Path
library=C.CDLL(str(Path(__file__).with_name('owned-shared-payload-copy-candidate.dll')))
library.nf_shared_payload_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
def copy_payload(memory,payload):
 if type(payload)is not bytes or not 0<len(payload)<=memory.size:raise ValueError('Invalid immutable shared payload')
 target=C.c_char.from_buffer(memory.buf)
 try:
  source=C.c_char_p(payload)
  status=library.nf_shared_payload_copy(C.addressof(target),memory.size,source,len(payload))
  if status!=1:raise ValueError('Native shared payload copy failed: '+str(status))
 finally:del target
