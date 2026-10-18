from pathlib import Path
import ctypes as C,random,struct,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));oracle=C.CDLL(str(p/'obj-oracle.dll'));d.nf_rect_window_layer.argtypes=[C.c_uint,C.c_void_p,C.c_void_p];oracle.nf_window_oracle.argtypes=[C.c_void_p]*3+[C.c_uint]+[C.c_void_p]*3;rng=random.Random(678);v=bytes(0x18000);pal=bytes(1024);o=bytearray(1024)
for i in range(128):struct.pack_into('<H',o,i*8,512)
for n in range(256):
 regs=(C.c_uint16*6)(*[rng.randrange(65536) for _ in range(6)]);display=0x1444|((n%4)<<13);out=(C.c_uint8*38400)();ref=(C.c_uint8*38400)();pixels=(C.c_uint32*38400)();assert d.nf_rect_window_layer(display,regs,out);assert oracle.nf_window_oracle(v,pal,bytes(o),display,regs,ref,pixels)
 assert bytes(out)==bytes(ref),(n,next((i,out[i],ref[i],list(regs)) for i in range(38400) if out[i]!=ref[i]))
sentinel=(C.c_uint8*38400)(*([123]*38400));assert not d.nf_rect_window_layer(0x9444,regs,sentinel) and bytes(sentinel)==bytes([123]*38400)
r=dict(result='PASS',cases=256,control_pixels=256*38400,atomic_rejections=1,scope='Original software renderer rectangular window control plane, overlap, wrapped and offscreen bounds; OBJ-window, effects composition and scanline changes not covered');(p/'rect-window-tests.json').write_text(json.dumps(r,indent=2));print(r)
