from pathlib import Path
import ctypes as C,os,json,hashlib,threading
import numpy as np
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-gpu-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'recipe-gpu-build-report.json').read_text());assert sha(out/'recipe-gpu.dll')==build['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;D=C.c_double
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(name,args,res=C.c_int):f=getattr(d,name);f.argtypes=args;f.restype=res;return f
op=fn('nf_pc_scene_gpu_open',[],P);close=fn('nf_pc_scene_gpu_close',[P],None);err=fn('nf_pc_scene_gpu_error',[],C.c_char_p);renderer=fn('nf_pc_scene_gpu_renderer',[P],C.c_char_p)
seed=fn('nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);read=fn('nf_pc_scene_gpu_read_target',[P,P,S]);submit=fn('nf_pc_scene_gpu_render_recipe',[P,P,P,P,S,U,U,P]);mesh=fn('nf_pc_recipe_mesh_ring',[P,U,S],P);mf=fn('nf_pc_recipe_mesh_free',[P],None);mat=fn('nf_pc_recipe_material_decode',[U,P,U,S],P);mtf=fn('nf_pc_recipe_material_free',[P],None)
y,i=np.indices((160,256));pal=np.empty((160,256,4),np.uint8);pal[:,:,0]=(i*37+y*11)%256;pal[:,:,1]=(i*13+y*19)%256;pal[:,:,2]=(i*7+y*3)%256;pal[:,:,3]=255;pb=pal.tobytes();zero=bytes(15136)
g=op();assert g,err();gpu=renderer(g).decode();cases=checked=ambiguous=guards=preserved=boundary_differences=0;rows=[]
def target(w,h):raw=C.create_string_buffer(w*h*4);assert read(g,raw,len(raw)),err();return np.frombuffer(raw.raw,np.uint8).reshape(h,w,4).copy()
def material(kind):
 values=[b'\0']*15;m=bytearray(48);m[36:40]=(2).to_bytes(2,'little')+(8 if kind==1 else 4).to_bytes(2,'little');values[3 if kind==1 else 4]=bytes(m)
 texture=np.arange(16,dtype=np.uint8).reshape(4,4);texture[0,1]=1;texture[0,2]=255
 if kind==1:
  storage=np.full((4,8),77,np.uint8);storage[:,:4]=texture;values[7]=storage.tobytes()
 else:values[8]=texture.tobytes();lookup=np.arange(4081,dtype=np.uint32).astype(np.uint8);lookup[16]=0;lookup[4080]=17;values[13]=lookup.tobytes()
 buffers=[C.create_string_buffer(v) for v in values];blocks=(Block*15)(*[Block(C.cast(v,P),len(values[j])) for j,v in enumerate(buffers)]);m=mat(kind,blocks,15,65536);assert m
 indices=texture.copy() if kind==1 else lookup[texture.astype(np.uint32)*16];states=np.ones((4,4),bool) if kind==1 else texture!=0
 return m,indices,states
try:
 for w,h,aw,ah in [(240,160,240,160),(1921,1081,1621,1081),(3840,2160,3240,2160)]:
  for perspective in [False,True]:
   xy=np.array([[20,20],[220,20],[220,140],[20,140]],float);q=1+xy[:,0]/512 if perspective else np.ones(4);uvq=np.column_stack([-.17+xy[:,0]/137,.13+xy[:,1]/113]);ring=np.column_stack([xy,np.full(4,128.),uvq/q[:,None],q]);raw=(D*24)(*ring.ravel());m=mesh(raw,4,65536);assert m
   for kind in [1,2]:
    material_handle,indices,states=material(kind)
    try:
     for clip in [(0,240,0,160),(47,193,54,119),(0,0,0,160)]:
      seedraw=C.create_string_buffer(w*h*4);assert seed(g,zero,len(zero),zero,len(zero),0,pb,len(pb),w,h,aw,ah,0,160,seedraw,len(seedraw)),err();before=np.frombuffer(seedraw.raw,np.uint8).reshape(h,w,4).copy();expected=before.copy()
      xx=(np.arange(aw)+.5)*240/aw;yy=(ah-np.arange(ah)-.5)*160/ah
      x=xx[None,:];y=yy[:,None];qq=1+x/512 if perspective else 1;uu=(-.17+x/137)/qq;vv=(.13+y/113)/qq
      tx=np.floor((uu%1)*4).astype(int);ty=np.floor((vv%1)*4).astype(int);sample=indices[ty,tx];write=states[ty,tx]
      inside=(x>=20)&(x<220)&(y>=20)&(y<140)&(x>=clip[0])&(x<clip[1])&(y>=clip[2])&(y<clip[3]);covered=inside&write;ry,rx=np.nonzero(covered);source_y=(((ah-ry)*2-1)*80)//ah;expected[ry,rx,:3]=pal[source_y,sample[ry,rx],:3];expected[ry,rx,3]=255
      c=(U*4)(*clip);assert submit(g,m,material_handle,pb,len(pb),aw,ah,c),err();actual=target(w,h)
      # Independent analytic UVq oracle; exclude only texel-boundary numerical ambiguity.
      near=(np.abs((uu*4)-np.rint(uu*4))<1e-4)|(np.abs((vv*4)-np.rint(vv*4))<1e-4);uncertain=np.zeros((h,w),bool);uncertain[:ah,:aw]=near&inside
      all_differences=np.any(actual!=expected,axis=2);boundary_differences+=int((all_differences&uncertain).sum());differences=all_differences&~uncertain;assert not differences.any(),(w,h,perspective,kind,clip,int(differences.sum()),np.argwhere(differences)[:5].tolist())
      untouched=np.ones((h,w),bool);untouched[:ah,:aw]=~inside;assert np.array_equal(actual[untouched],before[untouched]);preserved+=int(untouched.sum());checked+=w*h-int(uncertain.sum());ambiguous+=int(uncertain.sum());cases+=1;rows.append(dict(size=[w,h,aw,ah],perspective=perspective,kind=kind,clip=clip,ambiguous_texel_boundary_pixels=int(uncertain.sum())))
     snapshot=target(w,h)
     for badclip,pn,badaw in [((10,9,0,160),len(pb),aw),((0,241,0,160),len(pb),aw),((0,240,0,160),len(pb)-1,aw),((0,240,0,160),len(pb),w+1)]:
      assert not submit(g,m,material_handle,pb,pn,badaw,ah,(U*4)(*badclip));assert np.array_equal(target(w,h),snapshot);guards+=1
     result=[]
     def other():result.append(submit(g,m,material_handle,pb,len(pb),aw,ah,(U*4)(0,240,0,160)))
     t=threading.Thread(target=other);t.start();t.join();assert result==[0] and np.array_equal(target(w,h),snapshot);guards+=1
    finally:mtf(material_handle)
   mf(m)
finally:close(g)
r=dict(result='PASS_RECIPE_GPU_EXPLICIT_CLIP_AND_INDEXED_MATERIAL_COMPONENT',renderer=gpu,cases=cases,pixels_compared=checked,pixels_excluded_near_texel_boundary=ambiguous,pixel_differences_within_excluded_texel_boundaries=boundary_differences,pixels_outside_clip_or_polygon_preserved=preserved,pixel_differences_outside_declared_ambiguity=0,negative_thread_and_input_guards=guards,dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),script_sha256=sha(Path(__file__)),scope='Synthetic rectangular recipe geometry; affine/perspective wrapping, source zero skip vs shade-mapped opaque zero, historical palette rows and explicit clip. Independent analytic pixel oracle. Existing shader, one GPU. Not real retained visibility/full scene.',full_scene_60fps=False,live_host_integration=False,rows=rows)
(out/'recipe-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
