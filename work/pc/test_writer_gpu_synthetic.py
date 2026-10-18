from pathlib import Path
import os,ctypes as C,json,hashlib
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-gpu-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=here/'test_recipe_writer_synthetic.py';source=original.read_text();marker='command=[0]*17;';assert source.count(marker)==1;hook='''captured=[]
original_check=check
def check(name,kind,command,texture,expected,shade=b'\\0'):
 original_check(name,kind,command,texture,expected,shade)
 captured.append((name,kind,list(command),texture,shade))
''';source=source.replace(marker,hook+marker);ref={'__file__':str(original),'__name__':'capture_verified_writer_fixtures'};exec(compile(source,str(original),'exec'),ref)
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;D=C.c_double
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-gpu.dll'))
def fn(n,args,res=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=res;return f
op=fn('nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);wf=fn('nf_pc_recipe_writer_free',[P],None);amap=fn('nf_pc_writer_address_map',[P,S],P);af=fn('nf_pc_writer_address_map_free',[P],None);ai=fn('nf_pc_writer_address_map_info',[P,P]);ab=fn('nf_pc_writer_address_map_buffer',[P,P,P]);open_gpu=fn('nf_pc_scene_gpu_open',[],P);close=fn('nf_pc_scene_gpu_close',[P],None);seed=fn('nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);read=fn('nf_pc_scene_gpu_read_target',[P,P,S]);draw=fn('nf_pc_scene_gpu_render_writer',[P,P,U,P,P,P,P,S,U,U,U,U]);error=fn('nf_pc_scene_gpu_error',[],C.c_char_p)
ring=(D*24)(0,0,128,0,0,1,240,0,128,240,0,1,240,160,128,240,160,1,0,160,128,0,160,1);bounds=(U*4)(0,240,0,160);yy,ii=np.indices((160,256));palette=np.empty((160,256,4),np.uint8);palette[:,:,0]=ii;palette[:,:,1]=(ii*13+yy*7)%256;palette[:,:,2]=(ii*29+yy*31)%256;palette[:,:,3]=255;pb=palette.tobytes();zero=bytes(15136);empty=bytes(163840);cases=list(ref['captured']);wall=cases[2];cases.append(('wall-entirely-source-zero',2,wall[2],bytes(65536),wall[4]));g=open_gpu();assert g;rows=[];guards=0;map_bytes=0
try:
 for name,kind,command,texture,shade in cases:
  keep,blocks=ref['fixture'](kind,command,texture,shade);w=op(ref['owner'],kind,ref['ordinal'],8,blocks,15,64*1024*1024);old=ref['op'](ref['owner'],kind,ref['ordinal'],8,blocks,15,64*1024*1024);assert w and old;m=amap(w,64*1024*1024);assert m;meta=(Q*15)();assert ai(m,meta);map_bytes+=meta[14];src_i=np.zeros((160,240),np.uint8);src_w=np.zeros((160,240),bool)
  try:
   for y in range(160):
    for x in range(240):result=(Q*4)();assert ref['sample'](old,x,y,result);src_i[y,x]=result[2];src_w[y,x]=bool(result[3])
   assert not amap(w,meta[14]-1);exact=amap(w,meta[14]);assert exact;af(exact);guards+=1
   for width,height,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
    sx=((np.arange(aw,dtype=np.int64)*2+1)*120)//aw;sy=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah;covered=src_w[sy[:,None],sx[None,:]];indices=src_i[sy[:,None],sx[None,:]]
    for mode in [1,0]:
     pixels=C.create_string_buffer(width*height*4);assert seed(g,zero,15136,zero,15136,0,empty,len(empty),width,height,aw,ah,0,0,pixels,len(pixels));assert draw(g,ring,4,bounds,w,m,pb,len(pb),aw,ah,1,mode),error();assert read(g,pixels,len(pixels));actual=np.frombuffer(pixels.raw,np.uint8).reshape(height,width,4);expected=np.zeros_like(actual);y,x=np.nonzero(covered);expected[y,x,3]=255
     if mode:expected[y,x,0]=indices[y,x]
     else:expected[y,x,:3]=palette[sy[y],indices[y,x],:3]
     assert np.array_equal(actual,expected),(name,width,mode,int(np.any(actual!=expected,axis=2).sum()));rows.append(dict(name=name,size=[width,height,aw,ah],index_mode=mode,pixels=width*height))
    snapshot=pixels.raw
    for palette_bytes,endpoint,index_mode,badaw in [(163839,1,0,aw),(163840,2,0,aw),(163840,1,2,aw),(163840,1,0,width+1)]:
     assert not draw(g,ring,4,bounds,w,m,pb,palette_bytes,badaw,ah,endpoint,index_mode);assert read(g,pixels,len(pixels)) and pixels.raw==snapshot;guards+=1
  finally:ref['free'](old);af(m);wf(w)
finally:close(g)
r=dict(result='PASS_GPU_WRITER_ZERO_LANES_WRAP_AND_STEP_RULES',cases=len(rows),pixels_compared=sum(r['pixels'] for r in rows),pixel_differences=0,invalid_descriptor_budget_palette_endpoint_mode_target_requests=guards,rows=rows,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),source_fixture_test_sha256=sha(original),executed_fixture_source_sha256=hashlib.sha256(source.encode()).hexdigest(),script_sha256=sha(Path(__file__)),core_opened=False,full_scene_60fps=False)
(out/'writer-gpu-synthetic-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
