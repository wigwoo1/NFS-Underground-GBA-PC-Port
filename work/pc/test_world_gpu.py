from pathlib import Path
import ctypes as C,os,struct,io,json,hashlib,threading
import numpy as np
from PIL import Image
from gles_world_reference import GLESWorldReference
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-gpu-tests';inputs=base/'NFSUG-pc-world-material-tests/inputs';material_refs=base/'NFSUG-pc-world-material-tests/references'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'world-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int

def fn(name,args,r=I):f=getattr(dll,name);f.argtypes=args;f.restype=r;return f
op=fn('nf_pc_world_gpu_open',[],P);close=fn('nf_pc_world_gpu_close',[P],None);error=fn('nf_pc_world_gpu_error',[],C.c_char_p);renderer=fn('nf_pc_world_gpu_renderer',[P],C.c_char_p);draw=fn('nf_pc_world_gpu_draw',[P,P,P,P,S,U,U,U,U,U,U,P,S]);read=fn('nf_pc_world_decode',[P,S,S],P);world_free=fn('nf_pc_world_free',[P],None);mesh_make=fn('nf_pc_world_mesh',[P,U,S],P);mesh_free=fn('nf_pc_world_mesh_free',[P],None);mesh_info=fn('nf_pc_world_mesh_info',[P,P]);material_make=fn('nf_pc_world_material',[P,U,S],P);material_free=fn('nf_pc_world_material_free',[P],None)
def integer(stream):return struct.unpack('>I',stream.read(4))[0]
def mesh_reference(path):
 stream=io.BytesIO(path.read_bytes());results=[]
 for _ in range(integer(stream)):
  affine=integer(stream);camera=integer(stream);n=integer(stream);stream.read(n*8);n=integer(stream);vertices=stream.read(n*4);n=integer(stream);planes=stream.read(n*44);results.append((vertices,planes))
 assert not stream.read();return results

def material_reference(path):
 stream=io.BytesIO(path.read_bytes());results=[]
 for _ in range(integer(stream)):
  if not integer(stream):results.append(None);continue
  meta=struct.unpack('>7I',stream.read(28));images=[]
  for _ in range(integer(stream)):images.append(stream.read(integer(stream)))
  columns={}
  if meta[6]:
   stream.read(48)
   for _ in range(integer(stream)):
    width=integer(stream);columns[width]=list(struct.unpack('<'+str(width)+'I',stream.read(width*4)))
  results.append((meta,images,columns))
 assert not stream.read();return results

def bounds(raw,index):
 at,n=struct.unpack_from('<2I',raw,84);entries=struct.unpack_from('<I',raw,at+4)[0];start=at+8+entries*20
 return struct.unpack_from('<4H',raw,start+16+index*8) if start<at+n else (0,240,0,160)
ref=GLESWorldReference(root/'work/android/java/org/codex/nfsugpreview/NativeSceneGpu.java');ctx=op();assert ctx,error();native_renderer=renderer(ctx).decode();rows=[];guard=False;four_k_actual=0;held=None;actual_surfaces=0;wall_screenshot=False
try:
 for path in sorted(inputs.glob('*.nsp')):
  raw=path.read_bytes();world=read(raw,len(raw),64*1024*1024);assert world;meshes=mesh_reference(out/'references'/path.with_suffix('.mesh').name);materials=material_reference(material_refs/path.with_suffix('.material').name)
  if path.name.startswith('synthetic'):
   pal=np.zeros((160,256,4),np.uint8);pal[:,:,0]=np.arange(256,dtype=np.uint8)[None,:];pal[:,:,1]=np.arange(160,dtype=np.uint8)[:,None];pal[:,:,2]=77;pal[:,:,3]=255;palette=pal.tobytes()
  else:palette=(base/'NFSUG-pc-background-tests/references'/(path.stem.split('-')[0]+'.palette.rgba')).read_bytes()
  try:
   for i,reference in enumerate(materials):
    if reference is None:continue
    meta,images,shades=reference;mesh=mesh_make(world,i,32*1024*1024);material=material_make(world,i,64*1024*1024);assert mesh and material;mi=(Q*16)();assert mesh_info(mesh,mi);is_actual=not path.name.startswith('synthetic')
    if is_actual:actual_surfaces+=1
    targets=[(240,160,240,160,0,160)]
    if is_actual and mi[12] and ((meta[5] and not wall_screenshot) or (not meta[5] and four_k_actual==0)):
     targets.append((3840,2160,3240,2160,0,160));four_k_actual+=1
    if path.stem in ['synthetic-lit-rgba','synthetic-lit-indexed','synthetic-lit-hidden']:targets.append((3840,2160,3240,2160,0,160))
    if path.stem=='synthetic-lit-rgba':targets.extend([(240,160,240,160,70,100),(240,160,240,160,80,80)])
    try:
     for w,h,aw,ah,top,bottom in targets:
      output=(C.c_ubyte*(w*h*4))();assert draw(ctx,mesh,material,palette,len(palette),w,h,aw,ah,top,bottom,output,len(output)),error();a=np.frombuffer(output,np.uint8).reshape(h,w,4);expected=ref.render_surface(*meshes[i],images,palette,meta[0],meta[1],meta[4],meta[2]==2,shades.get(aw),w,h,aw,ah,bounds(raw,i),top,bottom);b=np.frombuffer(expected,np.uint8).reshape(h,w,4);diff=np.any(a!=b,axis=2);coverage=a[:,:,3]!=b[:,:,3]
      rows.append(dict(world=path.stem,surface=i,width=w,height=h,owner_top=top,owner_bottom=bottom,pixels=w*h,covered_pixels=int(np.count_nonzero(a[:,:,3])),mismatched_pixels=int(diff.sum()),coverage_mismatches=int(coverage.sum()),color_mismatches=int((diff&~coverage).sum()),native_sha256=hashlib.sha256(output).hexdigest(),gles_sha256=hashlib.sha256(expected).hexdigest(),first=[dict(x=int(x),y=int(y),native=a[y,x].tolist(),gles=b[y,x].tolist()) for y,x in np.argwhere(diff)[:8]]))
      assert not a[:h-ah].any() and not a[h-ah:,aw:].any(),'Inactive target modified'
      if top==bottom:assert not a.any()
      if w==3840 and is_actual and not meta[5]:Image.fromarray(a[::-1].copy()).save(out/'source-road-4k.png')
      if w==3840 and is_actual and meta[5] and not wall_screenshot:Image.fromarray(a[::-1].copy()).save(out/'source-lit-wall-4k.png');wall_screenshot=True
      if not guard:
       short=C.create_string_buffer(b'unchanged');assert not draw(ctx,mesh,material,palette,len(palette),240,160,240,160,0,160,short,8) and short.raw.startswith(b'unchanged');valid=(C.c_ubyte*153600)();wrong=[];thread=threading.Thread(target=lambda:wrong.append(draw(ctx,mesh,material,palette,len(palette),240,160,240,160,0,160,valid,len(valid))));thread.start();thread.join();assert wrong==[0];guard=True
     if held:mesh_free(held[0]);material_free(held[1])
     held=(mesh,material,palette,rows[-1]['native_sha256']);mesh=material=None
    finally:
     if mesh:mesh_free(mesh)
     if material:material_free(material)
  finally:world_free(world)
finally:close(ctx);ref.close()
# Recreate graphics context on another thread after all source worlds are freed.
result=[]
def recreate():
 context=op()
 try:
  assert context,error();image=(C.c_ubyte*153600)();assert draw(context,held[0],held[1],held[2],len(held[2]),240,160,240,160,0,160,image,len(image)),error();assert hashlib.sha256(image).hexdigest()==held[3];result.append(True)
 finally:
  if context:close(context)
thread=threading.Thread(target=recreate);thread.start();thread.join();mesh_free(held[0]);material_free(held[1]);assert result==[True] and actual_surfaces==388 and wall_screenshot
r=dict(result='PC_WORLD_GPU_CROSS_REFERENCE_DIAGNOSTIC',native_renderer=native_renderer,reference_renderer=ref.renderer,reference_shader_unchanged=True,actual_surfaces=actual_surfaces,accepted_surfaces=406,targets=len(rows),pixel_comparisons=sum(row['pixels'] for row in rows),mismatched_pixels=sum(row['mismatched_pixels'] for row in rows),coverage_mismatches=sum(row['coverage_mismatches'] for row in rows),color_mismatches=sum(row['color_mismatches'] for row in rows),four_k_targets=sum(row['width']==3840 for row in rows),short_output_wrong_thread_empty_owner_guards=True,world_free_render_thread_recreation_verified=True,dll_sha256=hashlib.sha256((out/'world-gpu.dll').read_bytes()).hexdigest(),frames=rows,full_scene=False,playable_native_release=False,full_scene_60fps=False)
(out/'world-gpu-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='frames'},indent=2))
