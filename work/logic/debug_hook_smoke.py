import ctypes as C, os
from pathlib import Path
base=Path(r"G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port")
rom=Path(r"G:\EXTRA DATA DRIVE\Desktop\Emulators\GBA\GBA ROMS\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba")
state=base/"work"/"logic"/"driving-diagnostic.state"; folder=base/"tryout"/"NFSUG-mGBA-Renderer-Preview-20261012"; dll=folder/"nfsprobe.dll"
os.add_dll_directory(str(folder)); d=C.CDLL(str(dll)); P=C.POINTER; U=C.c_uint32; I=C.c_int
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_init.restype=I;d.nf_state.argtypes=[C.c_char_p,I];d.nf_state.restype=I;d.nf_calls.argtypes=[C.c_char_p];d.nf_debug.argtypes=[U];d.nf_frame.argtypes=[U];d.nf_debug_data.argtypes=[P(I)];d.nf_debug_data.restype=P(U);d.nf_close.argtypes=[]
assert d.nf_init(str(rom).encode(),b"");assert d.nf_state(str(state).encode(),0)
d.nf_calls(str(base/"work"/"logic"/"hook-smoke.csv").encode());d.nf_debug(0x080095E8)
for i in range(1,6):
 d.nf_frame(33); n=I(); ptr=d.nf_debug_data(C.byref(n)); print(i,n.value,hex(ptr[0]) if n.value else "",hex(ptr[15]) if n.value else "")
d.nf_calls(None);d.nf_close()