"""Opt-in shared input read into fresh, unpublished immutable bytes storage."""
import ctypes as C
from owned_shared_payload_copy_binding_candidate import library
allocate=C.pythonapi.PyBytes_FromStringAndSize
allocate.argtypes=[C.c_void_p,C.c_ssize_t];allocate.restype=C.py_object
address=C.pythonapi.PyBytes_AsString
address.argtypes=[C.py_object];address.restype=C.c_void_p

def copy_private(memory,size):
 if type(size)is not int or not 0<size<=memory.size or size>64*1024*1024:raise ValueError('Invalid private input extent')
 # Fresh bytes never escapes until the synchronous copy completes; no hash/read before fill.
 payload=allocate(None,size)
 source=C.c_char.from_buffer(memory.buf)
 try:
  status=library.nf_shared_payload_copy(address(payload),size,C.addressof(source),size)
  if status!=1:raise ValueError('Native private input copy failed: '+str(status))
 finally:del source
 return payload
