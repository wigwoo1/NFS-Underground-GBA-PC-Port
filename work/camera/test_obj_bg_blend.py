from pathlib import Path
import ctypes as C,struct,random,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));oracle=C.CDLL(str(p/'obj-oracle.dll'));f=d.nf_obj_bg_pixel;f.argtypes=[C.c_uint32]*3+[C.c_uint]*4;f.restype=C.c_uint32;oracle.nf_obj_bg_oracle.argtypes=[C.c_void_p]*3+[C.c_uint]*5+[C.c_void_p];rng=random.Random(675)
def expand(c):return sum(((((c>>j)&31)<<3)|(((c>>j)&31)>>2))<<k for j,k in [(0,0),(5,8),(10,16)])|0xff000000
for n in range(256):
 v=bytearray([1]*(0x18000));v[0x10000+512*32:0x10000+513*32]=b'\x11'*32;pal=bytearray(1024);bg=rng.randrange(32768);obj=rng.randrange(32768);struct.pack_into('<H',pal,2,bg);struct.pack_into('<H',pal,514,obj);o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 mode=n%2;priority=(n//2)%4;bp=(n//8)%4;effect=(n//32)%4;blend=(effect<<6)|((n//128)*0x14)|0x1400;alpha=rng.randrange(32)|(rng.randrange(32)<<8);brightness=rng.randrange(32);struct.pack_into('<3H',o,0,40|(mode<<10),40,512|(priority<<10));ref=(C.c_uint32*(240*160))();assert oracle.nf_obj_bg_oracle(bytes(v),bytes(pal),bytes(o),0x1444,bp,blend,alpha,brightness,ref);actual=ref[40*240+40]&0xffffff;expected=f(expand(obj),priority|(mode<<2),expand(bg),bp,blend,alpha,brightness)&0xffffff;assert actual==expected,(n,hex(actual),hex(expected),priority,bp,effect,mode)
r=dict(result='PASS',cases=256,scope='Two-candidateOBJ/BG2priority/effects pixel oracle; windows/backdrop/scanline state/multiplecandidatesnotverified');(p/'obj-bg-blend-tests.json').write_text(json.dumps(r,indent=2));print(r)
