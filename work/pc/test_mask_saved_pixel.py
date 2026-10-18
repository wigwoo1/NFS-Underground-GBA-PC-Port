from pathlib import Path
import os,json,ctypes as C,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-region-mask-tests';out=base/'NFSUG-pc-region-mask-edges-tests';case=json.loads((prior/'mask-near-failure-case.json').read_text());P=C.c_void_p;S=C.c_size_t;U=C.c_uint;D=C.c_double

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[]
for label,folder in [('failing_reference',prior),('direct_edges',out)]:
 with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(folder/'recipe-gpu.dll'))
 def fn(n,args,res=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=res;return f
 op=fn('nf_pc_scene_gpu_open',[],P);close=fn('nf_pc_scene_gpu_close',[P],None);seed=fn('nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);submit=fn('nf_pc_scene_gpu_render_coverage_mask',[P,P,U,P,P,U,U,U]);read=fn('nf_pc_scene_gpu_read_target',[P,P,S]);g=op();assert g;w,h,aw,ah=case['size'];flat=[x for v in case['ring'] for x in v];ring=(D*len(flat))(*flat);pixels=C.create_string_buffer(w*h*4);zero=bytes(15136);pal=bytes(163840)
 try:
  assert seed(g,zero,15136,zero,15136,0,pal,163840,w,h,aw,ah,0,0,pixels,len(pixels));assert submit(g,ring,len(case['ring']),(U*4)(*case['source_bounds']),bytes(case['color']),aw,ah,0);assert read(g,pixels,len(pixels));actual=[]
  for pixel in case['bad_pixels']:x,y=pixel['target_bottom_up_xy'];offset=(y*w+x)*4;actual.append(list(pixels.raw[offset:offset+4]))
  if label=='failing_reference':assert actual==[p['actual_rgba'] for p in case['bad_pixels']]
  else:assert actual==[case['color'] for p in case['bad_pixels']]
  rows.append(dict(variant=label,pixels=actual,dll_sha256=sha(folder/'recipe-gpu.dll')))
 finally:close(g)
r=dict(result='PASS_SAVED_PIXEL_FAILURE_REPRODUCED_AND_FIXED',rows=rows,case_sha256=sha(prior/'mask-near-failure-case.json'),script_sha256=sha(Path(__file__)),core_opened=False,tolerance_changed=False,full_scene_60fps=False);(out/'saved-pixel-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
