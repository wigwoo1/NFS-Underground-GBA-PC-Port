"""Synchronous native shared writes; exported source/destination spans stay owned."""
import ctypes as C,struct
from owned_shared_payload import parts
from owned_shared_blob import _HEADER,_MAGIC
class Buffer(C.Structure):
 _fields_=[('buf',C.c_void_p),('obj',C.c_void_p),('len',C.c_ssize_t),('itemsize',C.c_ssize_t),('readonly',C.c_int),('ndim',C.c_int),('format',C.c_char_p),('shape',C.POINTER(C.c_ssize_t)),('strides',C.POINTER(C.c_ssize_t)),('suboffsets',C.POINTER(C.c_ssize_t)),('internal',C.c_void_p)]
get_buffer=C.pythonapi.PyObject_GetBuffer;get_buffer.argtypes=[C.py_object,C.POINTER(Buffer),C.c_int];get_buffer.restype=C.c_int
release_buffer=C.pythonapi.PyBuffer_Release;release_buffer.argtypes=[C.POINTER(Buffer)];release_buffer.restype=None

def write_payload(memory,payload,generation,serial):
 metadata,blobs=parts(payload);sizes=[len(x) for x in blobs]
 directory=struct.pack('<2I',len(metadata),len(blobs))+struct.pack('<'+'I'*len(sizes),*sizes)
 total=len(directory)+len(metadata)+sum(sizes)
 if total>min(64*1024*1024,memory.size-_HEADER.size):raise ValueError('Shared output budget exceeded')
 destination=Buffer();get_buffer(memory.buf,C.byref(destination),0)
 try:
  at=_HEADER.size
  for section in (directory,metadata,*blobs):
   source=Buffer();get_buffer(section,C.byref(source),0)
   try:
    if source.len!=len(section) or not source.readonly or at+source.len>destination.len:raise ValueError('Invalid owned shared span')
    if source.len:C.memmove(destination.buf+at,source.buf,source.len)
    at+=source.len
   finally:release_buffer(C.byref(source))
  _HEADER.pack_into(memory.buf,0,_MAGIC,generation,serial,total)
 finally:release_buffer(C.byref(destination))
 return memory.name,generation,serial,total
