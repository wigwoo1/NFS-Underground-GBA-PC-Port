from pathlib import Path
import ctypes as C,random,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));d.nf_obj_tile.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p];rng=random.Random(971)
for n in range(400):
 v=bytearray(rng.randbytes(0x18000));pal=rng.randbytes(1024);tile=rng.randrange(512,1024);mode=n%2;bank=rng.randrange(16);out=(C.c_uint32*64)();assert d.nf_obj_tile(bytes(v),len(v),pal,len(pal),tile,mode,bank,1,out)
 base=0x10000+(tile&~1 if mode else tile)*32;expected=[]
 for i in range(64):
  index=v[base+i] if mode else (v[base+i//2]//(16 if i%2 else 1))%16
  c=int.from_bytes(pal[512+2*(index+(0 if mode else bank*16)):514+2*(index+(0 if mode else bank*16))],'little');parts=[(c>>j)&31 for j in (0,5,10)];expected.append(0 if index==0 else sum(((x<<3)|(x>>2))<<(8*j) for j,x in enumerate(parts))|0xff000000)
 assert list(out)==expected
for tile,mode,bank,bitmap,vn,pn in [(511,0,0,1,0x18000,1024),(1024,0,0,0,0x18000,1024),(512,2,0,1,0x18000,1024),(512,0,16,1,0x18000,1024),(512,0,0,1,0x17fff,1024),(512,0,0,1,0x18000,1023)]:
 out=(C.c_uint32*64)(*([0x12345678]*64));assert not d.nf_obj_tile(bytes(v),vn,pal,pn,tile,mode,bank,bitmap,out) and list(out)==[0x12345678]*64
r=dict(result='PASS',random_tile_cases=400,atomic_rejections=6,scope='Native4/8bppOBJtile indices/palette/transparency decoder,independentanalytic oracle; sprite positioning/affine/window/blend/composition notimplemented');(p/'obj-tile-tests.json').write_text(json.dumps(r,indent=2));print(r)
