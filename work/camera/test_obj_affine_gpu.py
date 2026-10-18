from pathlib import Path
import ctypes as C,struct,subprocess,json,numpy as np,random,hashlib
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));d.nf_obj_image.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]+[C.c_uint16]*4+[C.c_void_p,C.c_size_t,C.c_void_p];rng=random.Random(680);v=rng.randbytes(0x18000);pal=rng.randbytes(1024);reports=[]
for index,m in enumerate(((256,0,0,256),(0,-256,256,0),(-256,0,0,256),(256,128,-64,256),(-121,177,89,344),(512,0,0,512),(128,0,0,128),(0,0,0,0))):
 o=bytearray(1024)
 for i in range(128):struct.pack_into('<H',o,i*8,512)
 a=40|256|512;b=40|(1<<14);c=512;struct.pack_into('<3H',o,0,a,b,c)
 for j,value in enumerate(m):struct.pack_into('<h',o,6+j*8,value)
 regs=bytearray(96);struct.pack_into('<H',regs,0,0x1044);row=struct.pack('<2I',1,0)+regs+bytes(24)+v+pal+o;source=p/'obj-affine-gpu-source.bin';source.write_bytes(row);target=p/'obj-affine-gpu.rgba';log=subprocess.check_output([str(p/'obj-gpu-preview.exe'),str(source),str(target),'--native-affine'],text=True)
 asset=(C.c_uint32*4096)();dims=(C.c_uint*2)();assert d.nf_obj_image(v,len(v),pal,len(pal),a&~0x300,b&~0x3000,c,0x1044,asset,4096,dims);w,h=dims;dw,dh=w*2,h*2;image=np.ctypeslib.as_array(asset)[:w*h].reshape(h,w)&0xffffff
 # Independent per-output-pixel inverse mapping, not original-grid affine image.
 xx=np.arange(3840,dtype=np.float32)+.5;yy=np.arange(2160,dtype=np.float32)+.5;x=(xx-(300+40*13.5))/13.5-.5-dw/2;y=(yy-40*13.5)/13.5-.5-dh/2
 sx=np.floor((m[0]*x[None,:]+m[1]*y[:,None])/256+w/2+.0001).astype(int);sy=np.floor((m[2]*x[None,:]+m[3]*y[:,None])/256+h/2+.0001).astype(int)
 valid=(sx>=0)&(sx<w)&(sy>=0)&(sy<h)&(xx[None,:]>=300+40*13.5-.01)&(xx[None,:]<300+(40+dw)*13.5-.01)&(yy[:,None]>=40*13.5-.01)&(yy[:,None]<(40+dh)*13.5-.01);expected=np.zeros((2160,3840),np.uint32);expected[valid]=image[sy[valid],sx[valid]];actual=np.fromfile(target,dtype=np.uint32).reshape(2160,3840)[::-1]&0xffffff;diff=actual!=expected;assert not diff.any(),(index,int(diff.sum()),np.argwhere(diff)[:4].tolist())
 reports.append(dict(matrix=m,target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),gpu=log.strip()))
r=dict(result='PASS',cases=8,target_pixels=8*3840*2160,scope='Native4K per-fragment affine sprite inverse sampling, including rotation/reflection/shear/fractional scales/singular matrix; no live HUD effects composition',samples=reports);(p/'obj-affine-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
