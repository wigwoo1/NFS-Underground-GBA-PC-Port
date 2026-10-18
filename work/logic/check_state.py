from pathlib import Path
import ctypes as C,hashlib,json
r=Path('work').resolve();d=C.CDLL(str(r/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'');rows=[]
for name in ['original','smooth']:
 assert d.nf_state(str(r/'logic'/f'{name}.state').encode(),0);entry={'mode':name}
 for label,a,n in [('ewram',0x2000000,0x40000),('iwram',0x3000000,0x8000),('vram',0x6000000,0x18000)]:
  p=r/'logic'/f'{name}-{label}.bin';d.nf_dump(str(p).encode(),a,n);entry[label]=hashlib.sha256(p.read_bytes()).hexdigest()
 rows.append(entry)
assert all(rows[0][k]==rows[1][k]for k in ['ewram','iwram','vram'])
result={'result':'PASS','frames':300,'matched_memory':['EWRAM','IWRAM','VRAM'],'runs':rows,'scope':'Two real-time host runs with the same held-accelerator inputs and initial state, smoothing on/off. This verifies the tested memory outcomes, not every rendering artifact.'};(r/'logic/logic-equivalence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));d.nf_close()
