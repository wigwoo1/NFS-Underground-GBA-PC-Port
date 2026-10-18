from pathlib import Path
import ctypes as C,json
r=Path('work').resolve();d=C.CDLL(str(r/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_read.restype=C.c_uint32
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'');results=[]
for mode,norm in [(0,0),(1,0),(1,1)]:
 d.nf_state(str(r/'driving.state').encode(),0);d.nf_60(mode);d.nf_normalize_steering(norm);rows=[]
 for i in range(60):
  d.nf_frame(33);car=d.nf_read(0x30000fc,4);phys=d.nf_read(car+0x8c,4);rows.append({'frame':i+1,'steering':C.c_int32(d.nf_read(phys+0x2c,4)).value,'x':C.c_int32(d.nf_read(car+12,4)).value,'z':C.c_int32(d.nf_read(car+20,4)).value})
 results.append({'mode60':bool(mode),'steering_normalization':bool(norm),'samples':rows});print(mode,norm,[x for x in rows if x['frame'] in [4,8,12,16,24,60]],flush=True)
(r/'logic/steering-tests.json').write_text(json.dumps(results,indent=2));d.nf_close()
