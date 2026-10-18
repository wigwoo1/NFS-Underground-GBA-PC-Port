"""Battery-memory boundary test on Windows; not Android execution."""
import ctypes as C, os, json, argparse
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--library",type=Path,required=True)
a.add_argument("--rom",type=Path,required=True)
a.add_argument("--report",type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):
 d=C.CDLL(str(a.library))
 d.nfa_core_open.argtypes=[C.c_char_p];d.nfa_core_open.restype=C.c_void_p
 d.nfa_core_close.argtypes=[C.c_void_p]
 d.nfa_core_battery_size.argtypes=[C.c_void_p];d.nfa_core_battery_size.restype=C.c_size_t
 d.nfa_core_copy_battery.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];d.nfa_core_copy_battery.restype=C.c_size_t
 d.nfa_core_load_battery.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 assert d.nfa_core_battery_size(None)==0
 checks=0
 for size in (512,8192,32768,65536,131072):
  original=bytes((i*37+size//512)%256 for i in range(size))
  h=d.nfa_core_open(os.fsencode(a.rom));assert h
  try:
   assert d.nfa_core_load_battery(h,original,size)
   assert d.nfa_core_battery_size(h)==size
   out=C.create_string_buffer(size)
   assert d.nfa_core_copy_battery(h,out,size)==size and out.raw==original
   out.raw=b"\xa5"*size
   assert d.nfa_core_copy_battery(h,out,size-1)==0 and out.raw==b"\xa5"*size
   assert not d.nfa_core_load_battery(h,original,size-1)
   other=8192 if size==512 else 512
   assert not d.nfa_core_load_battery(h,bytes(other),other)
   assert not d.nfa_core_load_battery(h,None,size)
   assert d.nfa_core_copy_battery(h,out,size)==size and out.raw==original
  finally:d.nfa_core_close(h)
  h=d.nfa_core_open(os.fsencode(a.rom));assert h
  try:
   assert d.nfa_core_load_battery(h,original,size)
   assert d.nfa_core_copy_battery(h,out,size)==size and out.raw==original
  finally:d.nfa_core_close(h)
  checks+=1
 a.report.write_text(json.dumps({"passed":True,"save_sizes_tested":checks,"short_buffer_unchanged":True,"invalid_restore_preserves_data":True,"reopen_restore":True,"scope":"Windows host memory boundary only; no disk persistence or Android runtime"},indent=2))
 print(a.report.read_text())
