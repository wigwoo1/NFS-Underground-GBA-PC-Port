from pathlib import Path
import ctypes as C,struct,random,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));oracle=C.CDLL(str(p/'obj-oracle.dll'));f=d.nf_obj_bg_backdrop_pixel;f.argtypes=[C.c_uint32]*3+[C.c_uint,C.c_uint32]+[C.c_uint]*3;f.restype=C.c_uint32;oracle.nf_obj_bg_oracle.argtypes=[C.c_void_p]*3+[C.c_uint]*5+[C.c_void_p];rng=random.Random(676)
def expand(c):return sum(((((c>>j)&31)<<3)|(((c>>j)&31)>>2))<<k for j,k in [(0,0),(5,8),(10,16)])|0xff000000
for n in range(1024):
 v=bytearray([1]*0x18000);v[0x10000+512*32:0x10000+513*32]=b'\x11'*32;pal=bytearray(1024);bg,obj,bd=[rng.randrange(32768) for _ in range(3)];struct.pack_into('<H',pal,0,bd);struct.pack_into('<H',pal,2,bg);struct.pack_into('<H',pal,514,obj);o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 mode=n%2;priority=rng.randrange(4);bp=rng.randrange(4);effect=(n//2)%4;blend=(effect<<6)|rng.choice([0,4,16,32,20,36,48,52])|rng.choice([0,4,16,32,20,36,48,52])*256;alpha=rng.randrange(32)|(rng.randrange(32)<<8);brightness=rng.randrange(32);hasobj=bool(n&8);hasbg=bool(n&16)
 if hasobj:struct.pack_into('<3H',o,0,40|(mode<<10),40,512|(priority<<10))
 if not hasbg:v[40*240+40]=0
 ref=(C.c_uint32*(240*160))();assert oracle.nf_obj_bg_oracle(bytes(v),bytes(pal),bytes(o),0x1444,bp,blend,alpha,brightness,ref)
 actual=ref[40*240+40]&0xffffff;expected=f(expand(obj) if hasobj else 0,priority|(mode<<2),expand(bg) if hasbg else 0,bp,expand(bd),blend,alpha,brightness)&0xffffff
 assert actual==expected,(n,hex(actual),hex(expected),hasobj,hasbg,hex(blend),mode,priority,bp)
r=dict(result='PASS',cases=1024,scope='OBJ/BG2/backdrop candidate presence, priorities, first/second targets and effects; no windows or scanline events');(p/'obj-backdrop-tests.json').write_text(json.dumps(r,indent=2));print(r)
