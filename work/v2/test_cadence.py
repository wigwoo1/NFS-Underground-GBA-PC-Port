from pathlib import Path
import ctypes as C,json,time
from PIL import Image
root=Path(__file__).resolve().parents[1];d=C.CDLL(str(root/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'');results=[]
for speed in [1,2,4,8]:
 assert d.nf_state(str(root/'race.state').encode(),0);d.nf_speed(speed);d.nf_scene_enable(1)
 changes=[];prev=d.nf_read(0x04000000,2)&16;t=time.perf_counter()
 for i in range(600):
  d.nf_frame(1);p=d.nf_read(0x04000000,2)&16
  if p!=prev:changes.append(i)
  prev=p
 Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB').save(root/'v2'/f'speed-{speed}.png')
 for a,n,name in [(0x03000000,0x8000,'iwram'),(0x02000000,0x40000,'ewram')]:d.nf_dump(str(root/'v2'/f'speed-{speed}-{name}.bin').encode(),a,n)
 results.append({'cpu_factor':speed,'page_flips':len(changes),'fps':len(changes)/(600/(16777216/280896)),'wall_seconds':time.perf_counter()-t,'flip_frames':changes})
 print({k:v for k,v in results[-1].items()if k!='flip_frames'},flush=True)
(root/'v2/cpu-cadence.json').write_text(json.dumps(results,indent=2));d.nf_close()
