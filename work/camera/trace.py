from pathlib import Path
import ctypes as C,json
r=Path('work').resolve();d=C.CDLL(str(r/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_debug_data.argtypes=[C.POINTER(C.c_int)];d.nf_debug_data.restype=C.POINTER(C.c_uint32)
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'');d.nf_state(str(r/'driving.state').encode(),0);d.nf_scene_enable(1);d.nf_debug(0x30032f0)
for i in range(12):d.nf_frame(1)
n=C.c_int();p=d.nf_debug_data(C.byref(n));rows=[[hex(p[i*16+j])for j in range(16)]for i in range(n.value)];(r/'camera/road-entry.json').write_text(json.dumps(rows,indent=2));print(n.value,rows[:3]);d.nf_close()
