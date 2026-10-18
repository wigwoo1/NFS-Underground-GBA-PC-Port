from pathlib import Path
import ctypes as C,json,sys
from PIL import Image
root=Path(__file__).resolve().parents[1]
class Vertex(C.Structure):_fields_=[(k,C.c_float)for k in ['x','y','s','t','q']]
class Poly(C.Structure):_fields_=[(k,C.c_uint32)for k in ['address','width','height','stride','count','kind','shade']]+[('v',Vertex*32)]
d=C.CDLL(str(root/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_pixels.restype=C.c_void_p;d.nf_scene.argtypes=[C.POINTER(C.c_int)];d.nf_scene.restype=C.POINTER(Poly)
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'');assert d.nf_state(str(root/'driving.state').encode(),0);d.nf_scene_enable(1)
for _ in range(60):d.nf_frame(1)
n=C.c_int();polys=d.nf_scene(C.byref(n));print('polys',n.value)
rows=[];textures={}
for i in range(n.value):
 p=polys[i];rows.append({k:getattr(p,k) for k in ['address','width','height','stride','count','kind']}|{'v':[[getattr(v,k)for k in ['x','y','s','t','q']]for v in p.v[:p.count]]})
 name=f'{p.address:x}-{p.width}-{p.height}-{p.stride}'
 if name not in textures:
  buf=(C.c_uint32*(p.width*p.height))();assert d.nf_texture(C.byref(p),buf)
  im=Image.frombytes('RGBA',(p.width,p.height),bytes(buf));im.save(root/'v2'/f'tex-{name}.png');textures[name]=True
out=root/'v2';(out/'scene.json').write_text(json.dumps(rows,indent=2))
Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB').save(out/'reference.png')
overlay=(C.c_uint32*(240*160))();d.nf_overlay(overlay);Image.frombytes('RGBA',(240,160),bytes(overlay)).save(out/'overlay.png')
print('kind counts',__import__('collections').Counter(p['kind']for p in rows),'textures',len(textures),'overlay pixels',sum(v!=0 for v in overlay));print(rows[:2]);d.nf_close()
