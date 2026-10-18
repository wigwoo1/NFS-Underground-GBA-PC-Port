import ctypes as C,struct,json
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'obj-tile-held-audit.dll'));P=C.c_void_p;Z=C.c_size_t;U=C.c_uint32;H=C.c_uint16
fn=d.nf_obj_window_scanline_prepared;fn.argtypes=[P,Z,P,Z,P,Z,H,U,P,U,U,P,P,P,P]
a=(p/'prototype-runs/threaded-prepared-68bbda4cba3646c483956036e096c49e-dense-01-owned-hud.bin').read_bytes();output=bytearray();counts=[]
for y in range(160):
 r=a[y*34944:(y+1)*34944];v=C.create_string_buffer(bytes(0x10000)+r[128:128+0x8000]);pal=C.create_string_buffer(r[128+0x8000:128+0x8000+1024]);o=C.create_string_buffer(r[-1024:]);regs=r[8:104];win=(H*6)(*struct.unpack_from('<6H',regs,64));colors=(U*240)();tags=(U*240)();ctl=(C.c_uint8*240)();bd=(C.c_uint8*240)();display=struct.unpack_from('<H',regs)[0];blend,alpha,bright=struct.unpack_from('<3H',regs,80)
 assert fn(v,0x18000,pal,1024,o,1024,display,y,win,blend,bright,colors,tags,ctl,bd)
 output.extend(bytes(colors));counts.append(sum(c!=0 for c in colors))
Image.frombytes('RGBA',(240,160),bytes(output)).resize((960,640)).save(p/'prototype-runs/held-hud-cpu-candidates.png')
r={'result':'PASS','rows':160,'decoded_candidates':sum(counts),'scope':'CPU OBJ candidate decode only, no original BG occlusion or GPU parity'};(p/'prototype-runs/held-hud-cpu-candidates.json').write_text(json.dumps(r,indent=2));print(r)
