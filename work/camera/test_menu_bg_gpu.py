"""Full physical RGBA comparison of source BG2 GPU sampling; no framebuffer input."""
import ctypes as C,hashlib,json,struct,subprocess,math
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/lifecycle-hardware';d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';checks=[]
for name in ['stage-0','stage-2','stage-6','menu-2','menu-4','menu-5']:
 state=p.parent/'fix-menu'/(name+'.state');before=hashlib.sha256(state.read_bytes()).hexdigest();assert d.nf_init(rom,b'') and d.nf_state(str(state).encode(),0) and d.nf_layer_queue_enable(1)
 try:
  for _ in range(40):d.nf_frame(0)
  epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest();buf=C.create_string_buffer(100480);rows=[]
  for y in range(160):assert d.nf_layer_queue_row(epoch,refresh,y,buf,100480);rows.append(buf.raw)
 finally:d.nf_close()
 source=out/(name+'-bg-source.bin');image=out/(name+'-bg-gpu.rgba');source.write_bytes(b''.join(rows));subprocess.run([str(p/'menu-bg-gpu-test.exe'),str(source),str(image)],check=True)
 actual=image.read_bytes();assert len(actual)==3840*2160*4;expected=bytearray();nonzero=0
 for y,r in enumerate(rows):
  display=struct.unpack_from('<H',r,8)[0];m=struct.unpack_from('<6i',r,104);line=bytearray(3840*4);page=128+(0xa000 if display&16 else 0)
  for x in range(240):
   u=(m[4]+m[0]*x)//256;v=(m[5]+m[2]*x)//256;index=r[page+v*240+u] if display&0x400 and 0<=u<240 and 0<=v<160 else 0
   if index:
    c=struct.unpack_from('<H',r,98432+index*2)[0];color=bytes([((c>>(k*5)&31)<<3)|(c>>(k*5)&31)>>2 for k in range(3)]+[255]);nonzero+=1
   else:color=b'\0'*4
   left=math.ceil(300+x*13.5-.5);right=math.ceil(300+(x+1)*13.5-.5);line[left*4:right*4]=color*(right-left)
  count=math.ceil((y+1)*13.5-.5)-math.ceil(y*13.5-.5);expected.extend(line*count)
 assert actual==expected,(name,next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b))
 assert hashlib.sha256(state.read_bytes()).hexdigest()==before
 checks.append(dict(checkpoint=name,physical_pixels=3840*2160,mismatches=0,nonzero_logical_samples=nonzero,rgba_sha256=hashlib.sha256(actual).hexdigest()));print(name,'PASS',flush=True)
(out/'menu-bg-gpu-report.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='GPU per-fragment source indexed BG2/affine/palette/transparent index0 only; independent CPU sampling compared every4K RGBA pixel. No OBJ/window/effects composition or live menus yet.'),indent=2))
