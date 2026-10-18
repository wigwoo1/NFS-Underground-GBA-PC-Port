"""Independent complete-target oracle for sky submission over existing pixels."""
from pathlib import Path
import ctypes as C,os,json,hashlib,math,threading
import numpy as np
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-sky-composition-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'sky-gpu-build-report.json').read_text());dll=out/'source-sky-gpu.dll';assert sha(dll)==receipt['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;D=C.c_double
def fn(name,args,result=C.c_int):
 f=getattr(d,name);f.argtypes=args;f.restype=result;return f
op=fn('nf_pc_scene_gpu_open',[],P);close=fn('nf_pc_scene_gpu_close',[P],None);error=fn('nf_pc_scene_gpu_error',[],C.c_char_p)
common=[P,P,S,P,S,D,P,S,U,U,U,U,U,U]
draw=fn('nf_pc_scene_gpu_draw_sky',common+[P,S]);submit=fn('nf_pc_scene_gpu_render_sky',common);read=fn('nf_pc_scene_gpu_read_target',[P,P,S]);renderer=fn('nf_pc_scene_gpu_renderer',[P],C.c_char_p)
idx=np.arange(15136,dtype=np.uint32);lo=((idx*17+5)%256).astype(np.uint8).tobytes();up=((idx*73+19)%256).astype(np.uint8).tobytes()
y,i=np.indices((160,256));palette=np.empty((160,256,4),dtype=np.uint8)
palette[:,:,0]=(i*37+y*11)%256;palette[:,:,1]=(i*i+y*19)%256;palette[:,:,2]=(i*13+y*y)%256;palette[:,:,3]=(i+y)%256
seed_palette=palette.copy();seed_palette[:,:,:3]^=255
def oracle(size,band,weight,pal):
 w,h,aw,ah=size;x=((np.arange(aw,dtype=np.int64)*2+1)*120)//aw;y=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah
 offset=y[:,None]*240+x[None,:]-10560;mask=(offset>=0)&(offset<15136)&(y[:,None]>=band[0])&(y[:,None]<band[1]);yy,xx=np.nonzero(mask);at=offset[mask]
 a=pal[y[yy],np.frombuffer(lo,dtype=np.uint8)[at],:3].astype(np.uint32);b=pal[y[yy],np.frombuffer(up,dtype=np.uint8)[at],:3].astype(np.uint32);q=int(math.floor(float(np.float32(weight))*65536+.5))
 colors=((a*(65536-q)+b*q+32768)//65536).astype(np.uint8);return yy,xx,colors
g=op();assert g,error();gpu=renderer(g).decode();cases=compared=preserved=guards=0;rows=[]
def target(size):
 raw=C.create_string_buffer(size[0]*size[1]*4);assert read(g,raw,len(raw)),error();return np.frombuffer(raw.raw,dtype=np.uint8).reshape(size[1],size[0],4).copy()
try:
 assert not submit(g,lo,15136,up,15136,.5,palette.tobytes(),163840,240,160,240,160,0,160);guards+=1
 for size in [(240,160,240,160),(1921,1081,1621,1081),(3840,2160,3240,2160)]:
  w,h,aw,ah=size;raw=C.create_string_buffer(w*h*4)
  for band,weight in [((64,96),.123456789),((107,108),.5),((0,0),1.),((44,108),0.)]:
   assert draw(g,lo,15136,up,15136,.875,seed_palette.tobytes(),163840,*size,0,160,raw,len(raw)),error()
   expected=np.frombuffer(raw.raw,dtype=np.uint8).reshape(h,w,4).copy();before=expected.copy()
   yy,xx,colors=oracle(size,band,weight,palette);expected[yy,xx,:3]=colors;expected[yy,xx,3]=255
   assert submit(g,lo,15136,up,15136,weight,palette.tobytes(),163840,*size,*band),error();actual=target(size)
   assert np.array_equal(actual,expected),(size,band,int(np.count_nonzero(np.any(actual!=expected,axis=2))))
   untouched=np.ones((h,w),dtype=bool);untouched[yy,xx]=False;assert np.array_equal(actual[untouched],before[untouched]);preserved+=int(untouched.sum());cases+=1;compared+=w*h
   rows.append(dict(size=size,band=band,weight=weight,covered=len(yy),outside_preserved=int(untouched.sum())))
  snapshot=target(size)
  for args in [(lo,15135,up,15136,.5,palette.tobytes(),163840,*size,0,160),(lo,15136,up,15136,float('nan'),palette.tobytes(),163840,*size,0,160),(lo,15136,up,15136,.5,palette.tobytes(),163840,w-1,h,aw,ah,0,160),(lo,15136,up,15136,.5,palette.tobytes(),163840,*size,100,99)]:
   assert not submit(g,*args);assert np.array_equal(target(size),snapshot);guards+=1
  result=[]
  def wrong_thread():result.append(submit(g,lo,15136,up,15136,.5,palette.tobytes(),163840,*size,0,160))
  t=threading.Thread(target=wrong_thread);t.start();t.join();assert result==[0] and np.array_equal(target(size),snapshot);guards+=1
  tiny=C.create_string_buffer(b'\xa5'*64);assert not read(g,tiny,64) and tiny.raw==b'\xa5'*64+b'\0';guards+=1
finally:close(g)
r=dict(result='PASS_NO_CLEAR_NO_READBACK_SKY_SUBMISSION_COMPONENT',renderer=gpu,cases=cases,pixels_compared=compared,pixels_outside_band_preserved=preserved,pixel_differences=0,invalid_requests_rejected=guards,existing_target_required=True,dll_sha256=sha(dll),build_report_sha256=sha(out/'sky-gpu-build-report.json'),test_source_sha256=sha(Path(__file__)),rows=rows,live_integration=False,full_scene_60fps=False,scope='Sky-over-sky synthetic target composition; full-target independent color oracle and outside-band preservation. Readback is separate and diagnostic. Not full-scene geometry/retention/HUD composition or live timing.')
(out/'sky-composition-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
