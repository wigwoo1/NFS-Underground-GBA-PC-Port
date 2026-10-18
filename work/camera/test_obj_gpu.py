from pathlib import Path
import ctypes as C,struct,subprocess,json,hashlib,numpy as np
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));d.nf_obj_layer.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16,C.c_void_p,C.c_void_p];reports=[]
for frame in (0,179,499,719):
 v=(p/f'layer-inventory-{frame}-vram.bin').read_bytes();pal=(p/f'layer-inventory-{frame}-palette.bin').read_bytes();o=(p/f'layer-inventory-{frame}-oam.bin').read_bytes();regs=bytearray((p/f'layer-inventory-{frame}-register-shadow.bin').read_bytes());struct.pack_into('<H',regs,0,0x1044);row=struct.pack('<2I',frame+1,0)+regs+struct.pack('<6i',256,0,0,256,0,0)+v+pal+o;source=p/f'obj-gpu-{frame}.bin';source.write_bytes(row);target=p/f'obj-gpu-{frame}.rgba';log=subprocess.check_output([str(p/'obj-gpu-preview.exe'),str(source),str(target)],text=True)
 colors=(C.c_uint32*38400)();tags=(C.c_uint32*38400)();assert d.nf_obj_layer(v,len(v),pal,len(pal),o,len(o),0x1044,colors,tags);plane=np.ctypeslib.as_array(colors).reshape(160,240)&0xffffff
 actual=np.fromfile(target,dtype=np.uint32).reshape(2160,3840)[::-1]&0xffffff;xs=np.floor((np.arange(3240)+.5)/13.5).astype(int);ys=np.floor((np.arange(2160)+.5)/13.5).astype(int);expected=plane[ys[:,None],xs[None,:]];different=actual[:,300:3540]!=expected
 assert not different.any(),(frame,int(different.sum()),np.argwhere(different)[:4].tolist());assert not actual[:,:300].any() and not actual[:,3540:].any()
 reports.append(dict(refresh=frame+1,output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),gpu=log.strip(),compared_target_pixels=3840*2160))
r=dict(result='PASS',samples=reports,scope='Direct native sprite asset quads on3840x2160GPUtarget vs native unblended candidate oracle; affine assets baked atoriginalpixelgrid; no HUD windows/BG/blending/live composition');(p/'obj-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
