from pathlib import Path
import ctypes as C
r=Path('work').resolve();d=C.CDLL(str(r/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_hist.argtypes=[C.c_char_p]
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'')
assert d.nf_state(str(r/'driving.state').encode(),0)
d.nf_watch(0x200c24c,0x120)
for i in range(180):d.nf_frame(1)
d.nf_hist(str(r/'camera/matrix-writers.csv').encode());d.nf_close()
print((r/'camera/matrix-writers.csv').read_text())
