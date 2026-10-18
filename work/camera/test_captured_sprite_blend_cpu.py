import ctypes as C,struct,json,hashlib
from pathlib import Path
from PIL import Image
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/captured-sprite-blend-cpu-20261007');cp.mkdir(exist_ok=True)
f=(p/'motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();h=struct.unpack_from('<6I2Q',f);gn,hn,bn,tn=h[2:6];stride=hn//160
actual=Image.open('outputs/nfsug-native-renderer/camera-research/checkpoints/cross-renderer-effect-isolation-20261007/original-source.png').convert('RGB')
under=Image.open('outputs/nfsug-native-renderer/camera-research/checkpoints/cross-renderer-neutral-hud-20261007/source.png').convert('RGB')
d=C.CDLL(str((p/'obj-tile.dll').resolve()));prepare=d.nf_obj_window_scanline_prepared;prepare.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16,C.c_uint,C.c_void_p,C.c_uint,C.c_uint]+[C.c_void_p]*4
blendfn=d.nf_obj_bg_backdrop_pixel;blendfn.argtypes=[C.c_uint32]*8;blendfn.restype=C.c_uint32
cache={};checks=0;bad=[];regs=[]
for y in range(2054,2133):
 row=int((y+.5)//13.5)
 if row not in cache:
  raw=f[40+gn+row*stride:40+gn+(row+1)*stride];r=raw[8:104];pal=raw[128+32768:128+32768+1024];oam=raw[128+32768+1024:];vram=bytes(65536)+raw[128:128+32768];display=struct.unpack_from('<H',r)[0];blend,alpha,bright=struct.unpack_from('<3H',r,80);priority=struct.unpack_from('<H',r,12)[0]&3;window=(C.c_uint16*6)(*struct.unpack_from('<6H',r,64));colors=(C.c_uint32*240)();tags=(C.c_uint32*240)();controls=(C.c_uint8*240)();backs=(C.c_uint8*240)()
  assert prepare(vram,len(vram),pal,len(pal),oam,len(oam),display,row,window,blend,bright,colors,tags,controls,backs)
  color=struct.unpack_from('<H',pal)[0];backdrop=0xff000000|sum((((color>>j)&31)<<3|((color>>j)&31)>>2)<<k for j,k in [(0,0),(5,8),(10,16)])
  cache[row]=(colors,tags,controls,blend,alpha,bright,priority,backdrop);regs.append(dict(row=row,blend=blend,alpha=alpha,brightness=bright))
 colors,tags,controls,blend,alpha,bright,priority,backdrop=cache[row]
 for x in range(3337,3445):
  col=int((x+.5-300)//13.5);control=controls[col];b=blend if control&32 else blend&~192;obj=colors[col] if control&16 else 0;bg=0xff000000|sum(c<<(8*i) for i,c in enumerate(under.getpixel((x,y)))) if control&4 else 0
  expected=blendfn(obj,tags[col]|0x20000,bg,priority,backdrop,b,alpha,bright);rgb=tuple((expected>>(8*i))&255 for i in range(3));got=actual.getpixel((x,y));checks+=1
  if rgb!=got:bad.append(dict(x=x,y=y,expected=rgb,actual=got))
result=dict(checked_pixels=checks,mismatches=len(bad),first_mismatches=bad[:10],registers=regs,result='PASS' if not bad else 'MISMATCH',scope='Captured8758sprite/window candidates and coefficients vs verified CPU effect on neutralized-HUD scene underlay; bounded lower-right area, not fullscene/fractional/scanout proof.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

assert checks==8532 and not bad, result
