from pathlib import Path
import ctypes as C,random,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));api=d.nf_obj_image;api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]+[C.c_uint16]*4+[C.c_void_p,C.c_size_t,C.c_void_p]
rng=random.Random(989);sizes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
for i in range(192):
 shape=i%3;size=(i//3)%4;color=(i//12)%2;mapping=(i//24)%2;flip=(i//48)%4;w,h=sizes[shape][size];tile=rng.randrange(512,1024);bank=rng.randrange(16);a=(shape<<14)|(color<<13);b=(size<<14)|(flip<<12);c=tile|(bank<<12);v=rng.randbytes(0x18000);pal=rng.randbytes(1024);out=(C.c_uint32*4096)();dims=(C.c_uint*2)();assert api(v,len(v),pal,len(pal),a,b,c,4|(mapping<<6),out,4096,dims) and list(dims)==[w,h]
 for y in range(h):
  for x in range(w):
   sx=w-1-x if flip&1 else x;sy=h-1-y if flip&2 else y;start=(tile&~int(color and not mapping))*32;tx=sx//8;ty=sy//8;stride=w//8*(2 if color else 1) if mapping else 32
   if mapping:addr=((start+(ty*stride+tx*(2 if color else 1))*32+(sy%8)*(8 if color else 4)+(sx%8)//(1 if color else 2))&32767)
   else:addr=((start&0x7c00)+ty*1024+((start+tx*(64 if color else 32))&1023)+(sy%8)*(8 if color else 4)+(sx%8)//(1 if color else 2))&32767
   index=v[0x10000+addr];index=index if color else (index>>(4*(sx%2)))&15;off=512+2*(index+(0 if color else bank*16));rgb=int.from_bytes(pal[off:off+2],'little');expected=0 if not index else 0xff000000|sum((((rgb>>j)&31)*8+((rgb>>j)&31)//4)<<k for j,k in [(0,0),(5,8),(10,16)]);assert out[y*w+x]==expected,(i,x,y)
# Independent concrete odd-base example: 1D retains tile513,2D uses512.
v=bytearray(0x18000);pal=bytearray(1024);v[0x10000+512*32]=1;v[0x10000+513*32]=2;pal[514:516]=(31).to_bytes(2,'little');pal[516:518]=(31<<10).to_bytes(2,'little')
for mapping,expected in ((0,0xff0000ff),(1,0xffff0000)):
 out=(C.c_uint32*4096)();dims=(C.c_uint*2)();assert api(bytes(v),len(v),bytes(pal),len(pal),8192,0,513,4|(mapping<<6),out,4096,dims) and out[0]==expected
r=dict(odd_base_alignment_cases=2,result='PASS',cases=192,scope='All regular sprite shapes/sizes,4/8bpp,1D/2Dmapping,flipsandwrapping; analytic byte-address oracle,not original composite oracle');(p/'obj-image-tests.json').write_text(json.dumps(r,indent=2));print(r)

