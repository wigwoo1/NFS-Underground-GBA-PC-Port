from pathlib import Path
import ctypes as C,random,struct,json
p=Path('work/camera').resolve();native=C.CDLL(str(p/'obj-tile.dll'));oracle=C.CDLL(str(p/'obj-oracle.dll'));native.nf_obj_layer.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16,C.c_void_p,C.c_void_p];oracle.nf_obj_oracle.argtypes=[C.c_void_p]*3+[C.c_uint,C.c_void_p];rng=random.Random(765)
def compare(v,pal,o,display):
 colors=(C.c_uint32*(240*160))();meta=(C.c_uint32*(240*160))();ref=(C.c_uint32*(240*160))();assert native.nf_obj_layer(v,len(v),pal,len(pal),o,len(o),display,colors,meta);assert oracle.nf_obj_oracle(v,pal,o,display,ref);rgb=int.from_bytes(pal[:2],'little');bg=sum(((((rgb>>j)&31)<<3)|(((rgb>>j)&31)>>2))<<k for j,k in [(0,0),(5,8),(10,16)])
 for i in range(240*160):assert (colors[i]&0xffffff if colors[i] else bg)==ref[i]&0xffffff,(i,hex(colors[i]),hex(ref[i]))
for n in range(96):
 v=rng.randbytes(0x18000);pal=rng.randbytes(1024);o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 for i in range(3):struct.pack_into('<3H',o,i*8,40,40+i*2,512+i+(rng.randrange(4)<<10))
 compare(v,pal,bytes(o),0x1044)
for frame in (0,179,499,719):
 v=(p/f'layer-inventory-{frame}-vram.bin').read_bytes();pal=(p/f'layer-inventory-{frame}-palette.bin').read_bytes();o=(p/f'layer-inventory-{frame}-oam.bin').read_bytes();compare(v,pal,o,0x1044)
colors=(C.c_uint32*(240*160))(*([123]*(240*160)));meta=(C.c_uint32*(240*160))(*([456]*(240*160)))
for vn,pn,on,display in ((0x17fff,1024,1024,0x1044),(0x18000,1023,1024,0x1044),(0x18000,1024,1023,0x1044),(0x18000,1024,1024,0x3044)):
 assert not native.nf_obj_layer(v,vn,pal,pn,o,on,display,colors,meta) and list(colors)==[123]*(240*160) and list(meta)==[456]*(240*160)
r=dict(atomic_rejections=4,result='PASS',random_overlap_cases=96,original_captured_layers=4,compared_pixels=100*240*160,scope='NativeOBJcandidatecolorplane exactoriginalsoftwareoracle withBG/windows/blendingdisabled; metadata/fullcompositionnotverified');(p/'obj-layer-tests.json').write_text(json.dumps(r,indent=2));print(r)
