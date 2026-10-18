"""Original Quick Race route from private main-menu checkpoint."""
import ctypes as C,hashlib,json,struct
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parent;out=p/'prototype-runs/menu-navigation';state=out/'start-release.state';before=hashlib.sha256(state.read_bytes()).hexdigest();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');raw=rom.read_bytes();d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_pixels.restype=C.c_void_p;assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);steps=[];ledger=[]
try:
 for label,count,key in [('main-ready',40,0)]+[(f'quick-{i}',2,1) if j==0 else (f'quick-{i}-release',240,0) for i in range(6) for j in range(2)]:
  for _ in range(count):d.nf_frame(key);ledger.append(key)
  mode=d.nf_read(0x03005f14,4);frontend=d.nf_read(0x03006710,1);handler=struct.unpack_from('<I',raw,0x653ae0+frontend*4)[0];Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).save(out/(label+'.png'));checkpoint=out/(label+'.state');assert d.nf_state(str(checkpoint).encode(),1);steps.append(dict(label=label,updates=len(ledger),mode=mode,frontend=frontend,handler=hex(handler),checkpoint=str(checkpoint)));print(label,mode,frontend,hex(handler),flush=True)
finally:d.nf_close()
assert hashlib.sha256(state.read_bytes()).hexdigest()==before
(out/'quick-route.json').write_text(json.dumps(dict(result='MEASURED',source=str(state),source_sha256=before,steps=steps,input_ledger=ledger,scope='Original baseline inputs, private derived checkpoints, no native rendering claim.'),indent=2))
