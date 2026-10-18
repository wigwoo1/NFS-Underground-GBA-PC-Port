import ctypes as C,csv,json
from pathlib import Path
p=Path('work/camera').resolve();d=C.CDLL(str(p/'sky-caller-probe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_image_copy_trace.argtypes=[C.c_char_p]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
out=p/'sky-caller-trace.csv'
assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'race.state').encode(),0)
try:
 assert d.nf_image_copy_trace(str(out).encode())
 for i in range(640):d.nf_frame(1|(32 if 80<=i<400 else 16 if 400<=i<600 else 0))
finally:d.nf_image_copy_trace(None);d.nf_close()
rows=list(csv.DictReader(out.open()));sky=[r for r in rows if int(r['source'],16)>=0x08359000 and int(r['source'],16)<0x08360000 and int(r['height'])==63]
assert sky
print(json.dumps(sky[:8],indent=2))
