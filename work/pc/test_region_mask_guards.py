from pathlib import Path
import ctypes as C,os,json,hashlib,threading
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-region-mask-tests')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((out/'recipe-gpu-build-report.json').read_text());assert sha(out/'recipe-gpu.dll')==b['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;D=C.c_double

def fn(n,args,res=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=res;return f
op=fn('nf_pc_scene_gpu_open',[],P);close=fn('nf_pc_scene_gpu_close',[P],None);submit=fn('nf_pc_scene_gpu_render_coverage_mask',[P,P,U,P,P,U,U,U]);seed=fn('nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);read=fn('nf_pc_scene_gpu_read_target',[P,P,S]);error=fn('nf_pc_scene_gpu_error',[],C.c_char_p)
ring=(D*24)(20,20,128,20,20,1,220,20,128,220,20,1,220,140,128,220,140,1,20,140,128,20,140,1);bounds=(U*4)(20,220,20,140);color=bytes([11,22,33,255]);g=op();assert g,error();guards=0
try:
 assert not submit(g,ring,4,bounds,color,240,160,1);guards+=1
 raw=C.create_string_buffer(153600);zero=bytes(15136);pal=bytes(163840);assert seed(g,zero,15136,zero,15136,0,pal,len(pal),240,160,240,160,0,0,raw,len(raw));assert submit(g,ring,4,bounds,color,240,160,1)
 assert read(g,raw,len(raw));snapshot=raw.raw
 def unchanged():assert read(g,raw,len(raw)) and raw.raw==snapshot
 for rp,n,bp,cp,w,h,endpoint in [(ring,7,bounds,color,240,160,1),(None,4,bounds,color,240,160,1),(ring,4,None,color,240,160,1),(ring,4,bounds,None,240,160,1),(ring,4,(U*4)(220,20,20,140),color,240,160,1),(ring,4,(U*4)(20,241,20,140),color,240,160,1),(ring,4,bounds,color,241,160,1),(ring,4,bounds,color,240,161,1),(ring,4,bounds,color,0,160,1),(ring,4,bounds,color,240,160,2)]:
  assert not submit(g,rp,n,bp,cp,w,h,endpoint);unchanged();guards+=1
 for index,value in [(0,float('nan')),(2,63.),(5,0.)]:
  bad=(D*24)(*ring);bad[index]=value;assert not submit(g,bad,4,bounds,color,240,160,1);unchanged();guards+=1
 results=[]
 def worker():results.append(submit(g,ring,4,bounds,color,240,160,1))
 t=threading.Thread(target=worker);t.start();t.join();assert results==[0];unchanged();guards+=1
 assert submit(g,None,0,bounds,color,240,160,0);unchanged()
finally:close(g)
r=dict(result='PASS_COVERAGE_MASK_GPU_INPUT_THREAD_AND_TARGET_GUARDS',invalid_requests_rejected_without_target_change=guards,empty_ring_preserves_target=True,dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'mask-guard-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
