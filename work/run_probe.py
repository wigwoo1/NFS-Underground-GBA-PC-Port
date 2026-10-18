from pathlib import Path
import ctypes as C,sys,json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
d=C.CDLL(str(ROOT/'nfsprobe.dll'))
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_pixels.restype=C.c_void_p
d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint
d.nf_reg.restype=C.c_uint
d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,str(ROOT/'display-writes.csv').encode())
frames=[]
def shot(label):
 im=Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB')
 im.save(ROOT/f'{label}.png');frames.append((label,im));print(label,hex(d.nf_read(0x4000000,2)),hex(d.nf_reg(15)))
def run(n,k=0):
 for _ in range(n):d.nf_frame(k)
def tap(k):run(12,k);run(180)
if len(sys.argv)>1:
 assert d.nf_state(str(ROOT/(sys.argv[1]+'.state')).encode(),0)
else:
 run(200);shot('boot200');run(300);shot('boot500')
for i,k in enumerate([int(v,0) for v in sys.argv[2:]] if len(sys.argv)>1 else [1,8,1,1,1,1,1,1,1,1]):
 tap(k);shot(f'step{i}')
d.nf_state(str(ROOT/'latest.state').encode(),1)
for a,n,name in [(0x03000000,0x8000,'iwram'),(0x02000000,0x40000,'ewram'),(0x06000000,0x18000,'vram')]:d.nf_dump(str(ROOT/(name+'.bin')).encode(),a,n)
d.nf_hist(str(ROOT/'vram-writers.csv').encode())
if frames:
 sheet=Image.new('RGB',(480,190*((len(frames)+1)//2)))
 for i,(label,im) in enumerate(frames):
  x=(i%2)*240;y=(i//2)*190;sheet.paste(im,(x,y));ImageDraw.Draw(sheet).text((x+3,y+163),label,fill='white')
 sheet.save(ROOT/'contact.png')
d.nf_close()

