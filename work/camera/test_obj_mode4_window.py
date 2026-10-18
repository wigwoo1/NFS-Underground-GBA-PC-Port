from pathlib import Path
import ctypes as C,struct,random,json
p=Path('work/camera').resolve();native=C.CDLL(str(p/'obj-tile.dll'));oracle=C.CDLL(str(p/'obj-oracle.dll'));f=native.nf_obj_mode4_window_layer;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]*5+[C.c_void_p]*3;oracle.nf_window_composite_oracle.argtypes=[C.c_void_p]*3+[C.c_uint]*5+[C.c_void_p]*3;rng=random.Random(677)
def compare(v,pal,o,display,bp,blend,alpha,y,label,captured=None,window_capture=None):
 windows=(C.c_uint16*6)(*[rng.randrange(65536) for _ in range(6)]);display|=0x6000;matrix=(C.c_int32*6)(rng.choice([-512,-256,-128,0,128,256,512]),rng.choice([-64,0,64]),rng.choice([-64,0,64]),rng.choice([-256,128,256,512]),rng.randrange(-240*256,240*256),rng.randrange(-160*256,160*256));
 if window_capture is not None:windows=(C.c_uint16*6)(*window_capture)
 if captured is not None:matrix=(C.c_int32*6)(*captured)
 out=(C.c_uint32*38400)();ref=(C.c_uint32*38400)();assert f(v,len(v),pal,len(pal),o,len(o),display,bp,blend,alpha,y,matrix,windows,out);assert oracle.nf_window_composite_oracle(v,pal,o,display,bp,blend,alpha,y,matrix,windows,ref)
 mask=(C.c_uint8*38400)();maskref=(C.c_uint8*38400)();junk=(C.c_uint32*38400)();native.nf_rect_window_layer(display,windows,mask);oracle.nf_window_oracle.argtypes=[C.c_void_p]*3+[C.c_uint]+[C.c_void_p]*3;oracle.nf_window_oracle(v,pal,o,display,windows,maskref,junk)
 for i in range(38400):assert out[i]&0xffffff==ref[i]&0xffffff,(label,i,hex(out[i]),hex(ref[i]),list(matrix),hex(blend),alpha,y,list(windows),mask[i],maskref[i])
for n in range(2048):
 v=rng.randbytes(0x18000);pal=rng.randbytes(1024);o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 for i in range(4):struct.pack_into('<3H',o,i*8,40|(rng.randrange(2)<<10),40+i*2,512+i+(rng.randrange(4)<<10))
 compare(v,pal,bytes(o),0x1444|((n%2)*16),rng.randrange(4),rng.randrange(64)|(rng.randrange(4)<<6)|(rng.randrange(64)<<8),rng.randrange(32)|(rng.randrange(32)<<8),rng.randrange(32),n)
for frame in (0,179,499,719):
 v=(p/f'layer-inventory-{frame}-vram.bin').read_bytes();pal=(p/f'layer-inventory-{frame}-palette.bin').read_bytes();o=(p/f'layer-inventory-{frame}-oam.bin').read_bytes();regs=(p/f'layer-inventory-{frame}-register-shadow.bin').read_bytes();get=lambda offset:struct.unpack_from('<H',regs,offset)[0]
 m=list(struct.unpack_from('<4h',regs,32));refs=list(struct.unpack_from('<2I',regs,40));refs=[((r&0xfffffff)^0x8000000)-0x8000000 for r in refs];compare(v,pal,o,0x1444|(get(0)&16),get(12)&3,get(80),get(82),get(84),frame,m+refs,list(struct.unpack_from('<6H',regs,64)))
sentinel=(C.c_uint32*38400)(*([123]*38400))
for display,bgcnt in ((0x1443,0),(0x9444,0),(0x14c4,0),(0x1444,64)):
 assert not f(v,len(v),pal,len(pal),o,len(o),display,bgcnt,0,0,0,(C.c_int32*6)(256,0,0,256,0,0),(C.c_uint16*6)(),sentinel) and list(sentinel)==[123]*38400
r=dict(atomic_rejections=4,result='PASS',random_overlap_compositions=2048,captured_compositions=4,pixels=2052*38400,scope='Random signed-affine mode4; captured palette/VRAM/OAM and color effects, rectangular windows included; OBJ-window/mosaic/scanline latches not covered');(p/'obj-mode4-window-tests.json').write_text(json.dumps(r,indent=2));print(r)




