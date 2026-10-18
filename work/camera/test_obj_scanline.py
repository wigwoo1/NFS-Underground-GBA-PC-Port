from pathlib import Path
import ctypes as C,struct,random,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'))
common=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]
d.nf_obj_layer.argtypes=common+[C.c_void_p]*2;d.nf_obj_scanline.argtypes=common+[C.c_uint,C.c_void_p,C.c_void_p]
d.nf_obj_layer_prepared.argtypes=common+[C.c_uint]*2+[C.c_void_p]*2;d.nf_obj_scanline_prepared.argtypes=common+[C.c_uint]*3+[C.c_void_p]*2
rng=random.Random(83011);checks=0
def check(v,pal,o,display,rows,blend=None,brightness=0):
 global checks
 full=(C.c_uint32*38400)();tags=(C.c_uint32*38400)()
 assert (d.nf_obj_layer(v,len(v),pal,len(pal),o,len(o),display,full,tags) if blend is None else d.nf_obj_layer_prepared(v,len(v),pal,len(pal),o,len(o),display,blend,brightness,full,tags))
 for y in rows:
  line=(C.c_uint32*240)();meta=(C.c_uint32*240)()
  assert (d.nf_obj_scanline(v,len(v),pal,len(pal),o,len(o),display,y,line,meta) if blend is None else d.nf_obj_scanline_prepared(v,len(v),pal,len(pal),o,len(o),display,y,blend,brightness,line,meta))
  assert bytes(line)==bytes(full)[y*960:(y+1)*960],('color',y)
  assert bytes(meta)==bytes(tags)[y*960:(y+1)*960],('metadata',y)
  checks+=240
data=(p/'hud-batch-captured.bin').read_bytes()
for y in range(160):
 b=data[y*34944:(y+1)*34944];v=bytes(65536)+b[128:128+32768];pal=b[32896:33920];o=b[33920:34944];check(v,pal,o,struct.unpack_from('<H',b,8)[0],[y])
for case in range(128):
 v=rng.randbytes(98304);pal=rng.randbytes(1024);o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 for i in range(12):
  affine=rng.randrange(2);a=rng.randrange(256)|(affine<<8)|((rng.randrange(2) if affine else 0)<<9)|(rng.randrange(2)<<10)|(rng.randrange(2)<<13)|(rng.randrange(3)<<14)
  b=rng.randrange(512)|(rng.randrange(32)<<9)|(rng.randrange(4)<<14);c=rng.randrange(512,1024)|(rng.randrange(4)<<10)|(rng.randrange(16)<<12);struct.pack_into('<3H',o,i*8,a,b,c)
 for i in range(32):
  for j in range(4):struct.pack_into('<h',o,i*32+6+j*8,rng.randrange(-768,769))
 check(v,pal,bytes(o),0x1004|(rng.randrange(2)<<6),[0,31,79,159])
 check(v,pal,bytes(o),0x1004|(rng.randrange(2)<<6),[0,31,79,159],rng.randrange(65536),rng.randrange(32))
out=C.create_string_buffer(b'Q'*960,960);meta=C.create_string_buffer(b'R'*960,960)
assert not d.nf_obj_scanline(v,len(v),pal,len(pal),bytes(o),len(o),0x1044,160,out,meta)
assert out.raw==b'Q'*960 and meta.raw==b'R'*960
r=dict(result='PASS',captured_rows=160,randomized_states=128,prepared_effect_states=128,checked_color_and_metadata_pixels=checks,atomic_rejections=1,scope='Direct regular/affine/wrapped scanline candidates and pre-overlap palette variants vs previously original-oracled full native layer including retained variant flags')
(p/'obj-scanline-tests.json').write_text(json.dumps(r,indent=2));print(r)
