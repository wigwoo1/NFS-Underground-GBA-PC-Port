from pathlib import Path
import ctypes as C,json,hashlib,time
from PIL import Image
ROOT=Path(__file__).resolve().parent
d=C.CDLL(str(ROOT/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'')
out=Path('outputs/nfsug-research');results=[];pictures=[]
for native in [0,1]:
 assert d.nf_state(str(ROOT/'race.state').encode(),0);d.nf_native(native)
 flips=0;old=d.nf_read(0x04000000,2)&16;start=time.perf_counter()
 for frame in range(3600):
  # Drive, coast, steer, brake, and accelerate again.
  k=1 if frame<1200 else (1|16 if frame<1250 else 1 if frame<1800 else 2 if frame<1860 else 1)
  d.nf_frame(k);page=d.nf_read(0x04000000,2)&16;flips+=page!=old;old=page
  if frame in [599,1799,3599]:
   im=Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB');im.save(ROOT/f'integration-{native}-{frame}.png')
 elapsed=time.perf_counter()-start
 state=ROOT/f'integration-{native}.state';assert d.nf_state(str(state).encode(),1)
 for _ in range(120):d.nf_frame(1)
 expected=C.string_at(d.nf_pixels(),240*160*4)
 assert d.nf_state(str(state).encode(),0)
 for _ in range(120):d.nf_frame(1)
 assert expected==C.string_at(d.nf_pixels(),240*160*4),'Save/load replay diverged'
 results.append({'native_span_enabled':bool(native),'vblanks':3600,'scene_page_flips':flips,'scene_fps':round(flips/(3600/(16777216/280896)),3),'headless_seconds':round(elapsed,3),'deterministic_save_load_replay':'PASS'})
print(json.dumps(results,indent=2));(out/'integration-tests.json').write_text(json.dumps(results,indent=2));d.nf_close()
