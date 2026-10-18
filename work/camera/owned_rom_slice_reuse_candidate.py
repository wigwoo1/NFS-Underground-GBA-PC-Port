"""Bounded thread-local reuse of proven unoverlaid immutable ROM slices."""
import threading
from collections import OrderedDict
local=threading.local()
def read_rom_slice(rom,offset,size):
 if type(rom) is not bytes:raise TypeError('Immutable ROM required')
 if offset<0 or size<0 or offset+size>len(rom):raise ValueError('Invalid ROM slice')
 if getattr(local,'rom',None) is not rom:
  local.rom=rom;local.entries=OrderedDict();local.bytes=0
 key=(offset,size);entries=local.entries
 if key in entries:
  value=entries.pop(key);entries[key]=value;return value
 value=rom[offset:offset+size]
 if size<=2*1024*1024:
  while entries and (len(entries)>=64 or local.bytes+size>2*1024*1024):local.bytes-=len(entries.popitem(last=False)[1])
  entries[key]=value;local.bytes+=size
 return value
def clear():
 local.rom=None;local.entries=OrderedDict();local.bytes=0
