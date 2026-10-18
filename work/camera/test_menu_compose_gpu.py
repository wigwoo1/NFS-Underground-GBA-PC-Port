"""Whole4K source asset composition versus independent CPU row compositor."""
import ctypes as C,hashlib,json,math,os,struct,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/lifecycle-hardware';d=C.CDLL(str(p/'obj-tile.dll'));f=d.nf_obj_mode4_window_scanline;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]*5+[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];pixel=d.nf_obj_bg_backdrop_pixel;pixel.argtypes=[C.c_uint32]*8;pixel.restype=C.c_uint32;checks=[]
for name in ['stage-0','stage-2','stage-6','menu-2','menu-4','menu-5']:
 source=out/(name+'-bg-source.bin');rows=source.read_bytes();image=out/(name+'-composed-gpu.rgba');run=subprocess.run([str(p/'menu-bg-gpu-test.exe'),str(source),str(image)],env=dict(os.environ,NF_MENU_COMPOSE='1',NF_MENU_OWNED='1',NF_MENU_REPEAT='1'),check=True,capture_output=True,text=True);assert 'expanded_source_freed=1' in run.stdout and 'stale_epoch_rejected_framebuffer_unchanged=1 compositor_initializations=1 frames=3' in run.stdout;actual=image.read_bytes();expected=bytearray()
 for y in range(160):
  r=rows[y*100480:(y+1)*100480];get=lambda offset:struct.unpack_from('<H',r,offset)[0];m=(C.c_int32*6)(*struct.unpack_from('<6i',r,104));window=(C.c_uint16*6)(*struct.unpack_from('<6H',r,72));decoded=(C.c_uint32*240)();v=r[128:98432];pal=r[98432:99456];o=r[99456:100480];assert f(v,len(v),pal,len(pal),o,len(o),get(8),get(20),get(88),get(90),get(92),m,window,y,decoded)
  c=get(98432);bd=0xff000000|sum((((c>>(k*5)&31)<<3)|(c>>(k*5)&31)>>2)<<(k*8) for k in range(3));side=struct.pack('<I',pixel(0,0,0,get(20)&3,bd,get(88),get(90),get(92)));line=bytearray(side*3840)
  for x in range(240):
   left=math.ceil(300+x*13.5-.5);right=math.ceil(300+(x+1)*13.5-.5);line[left*4:right*4]=struct.pack('<I',decoded[x])*(right-left)
  expected.extend(line*(math.ceil((y+1)*13.5-.5)-math.ceil(y*13.5-.5)))
 mismatches=sum(a!=b for a,b in zip(actual,expected));assert len(actual)==len(expected)==3840*2160*4
 if mismatches:print(name,'FAIL',mismatches,next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),flush=True)
 else:print(name,'PASS',flush=True)
 checks.append(dict(checkpoint=name,owned_snapshot=True,repeated_frames=3,compositor_initializations=1,expanded_source_freed=True,stale_epoch_rejected_framebuffer_unchanged=True,mismatched_bytes=mismatches,rgba_sha256=hashlib.sha256(actual).hexdigest()))
report=dict(result='PASS' if all(c['mismatched_bytes']==0 for c in checks) else 'FAIL',checks=checks,scope='Full4K GPU source bitmap/OBJ/window/effects composition versus independent CPU row compositor; source assets only. Static captured snapshots, no live timing claim.');(out/'menu-compose-gpu-report.json').write_text(json.dumps(report,indent=2));assert report['result']=='PASS'
