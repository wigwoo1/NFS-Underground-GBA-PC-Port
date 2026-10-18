"""Borrowed immutable sparse memory retained for synchronous native calls."""
import ctypes as C
from pathlib import Path
class Range(C.Structure):_fields_=[('address',C.c_uint32),('size',C.c_size_t),('data',C.c_void_p)]
class Context(C.Structure):_fields_=[('rom',C.c_void_p),('rom_size',C.c_size_t),('ranges',C.POINTER(Range)),('count',C.c_size_t)]
class NativeSparseReader:
 def __init__(self,memory,callback_type):
  if not isinstance(memory.rom,bytes):raise ValueError('Native ROM must be immutable')
  self.rom=C.c_char_p(memory.rom);self.payloads=[];entries=[];end=0
  for address,data in memory._ranges:
   if not isinstance(data,bytes) or not data or address<end or address+len(data)>0x100000000:raise ValueError('Invalid immutable sparse ranges')
   pointer=C.c_char_p(data);self.payloads.append(pointer);entries.append(Range(address,len(data),C.cast(pointer,C.c_void_p)));end=address+len(data)
  self.ranges=(Range*len(entries))(*entries)
  self.context=Context(C.cast(self.rom,C.c_void_p),len(memory.rom),self.ranges,len(entries))
  self.library=C.CDLL(str(Path(__file__).with_name('owned-sparse-reader.dll').resolve()))
  self.callback=C.cast(self.library.nf_owned_sparse_read,callback_type)
  self.pointer=C.byref(self.context)

def reader_for_memory(memory,callback_type):
 existing=getattr(memory,'_native_road_reader',None)
 if existing is None:
  existing=NativeSparseReader(memory,callback_type);memory._native_road_reader=existing
 return existing
