from pathlib import Path
import ctypes as C, os, json, hashlib, math, threading, struct
import numpy as np
from PIL import Image
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-model-tests');refs=out/'references'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'model-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;I=C.c_int

def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn('nf_pc_model_gpu_open',[],P);close=fn('nf_pc_model_gpu_close',[P],None);err=fn('nf_pc_model_gpu_error',[],C.c_char_p);renderer=fn('nf_pc_model_gpu_renderer',[P],C.c_char_p);decode=fn('nf_pc_model_mesh_decode',[P,S,S],P);free=fn('nf_pc_model_mesh_free',[P],None);draw=fn('nf_pc_model_gpu_draw',[P,P,P,S,U,U,U,U,U,U,P,S])

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cpu(name,m,palette,w,h,aw,ah,top,bottom):
 vertices=np.frombuffer((refs/(name+'.vertices')).read_bytes(),'<f4').reshape(-1,3,5);planes=np.frombuffer((refs/(name+'.planes')).read_bytes(),'<f4').reshape(-1,11)
 tex=np.frombuffer((refs/(name+('.indices' if m[5] else '.rgba'))).read_bytes(),np.uint8).reshape((m[1],m[0]) if m[5] else (m[1],m[0],4));pal=np.frombuffer(palette,np.uint8).reshape(160,256,4)
 image=np.zeros((h,w,4),np.uint8)
 for tri,plane in zip(vertices,planes):
  xy=tri[:,:2].astype(np.float64)*[aw/240,ah/160]
  x0=max(0,int(math.floor(xy[:,0].min())));x1=min(aw,int(math.ceil(xy[:,0].max())));y0=max(int(math.ceil(top*ah/160-.5)),0,int(math.floor(xy[:,1].min())));y1=min(int(math.ceil(bottom*ah/160-.5)),ah,int(math.ceil(xy[:,1].max())))
  if x1<=x0 or y1<=y0:continue
  xx=np.arange(x0,x1)[None,:]+.5;yy=np.arange(y0,y1)[:,None]+.5
  edges=[(b[0]-a[0])*(yy-a[1])-(b[1]-a[1])*(xx-a[0]) for a,b in zip(xy,np.roll(xy,-1,axis=0))]
  inside=(edges[0]<=0)&(edges[1]<=0)&(edges[2]<=0)
  # Shader arithmetic uses float32; coverage above remains independent float64 geometry.
  dx=(xx.astype(np.float32)*np.float32(240/aw)-plane[0]);dy=(yy.astype(np.float32)*np.float32(160/ah)-plane[1]);uvq=plane[2:5]+plane[5:8]*dx[...,None]+plane[8:11]*dy[...,None]
  uv=uvq[:,:,:2]/uvq[:,:,2:3];uv-=np.floor(uv);tx=np.minimum((uv[:,:,0]*m[0]).astype(int),m[0]-1);ty=np.minimum((uv[:,:,1]*m[1]).astype(int),m[1]-1)
  rows=np.broadcast_to(np.minimum((yy*160/ah).astype(int),159),inside.shape)
  colors=pal[rows,tex[ty,tx]] if m[5] else tex[ty,tx].copy()
  if not m[5]:colors=np.where((colors[:,:,3]<128)[:,:,None],pal[rows,0],colors)
  colors[:,:,3]=255;region=image[y0:y1,x0:x1];region[inside]=colors[inside]
 return image[::-1].copy()
ctx=op();assert ctx,err();gpu=renderer(ctx).decode();results=[];guard=False;held=None
try:
 for line in (refs/'models.txt').read_text().splitlines():
  fields=line.split();name=fields[0];m=list(map(int,fields[1:]));raw=(refs/(name+'.model')).read_bytes();mesh=decode(raw,len(raw),32*1024*1024);assert mesh
  if name.startswith('synthetic'):palette=np.zeros((160,256,4),np.uint8);palette[:,:,0]=np.arange(256,dtype=np.uint8)[None,:];palette[:,:,1]=np.arange(160,dtype=np.uint8)[:,None];palette[:,:,2]=77;palette[:,:,3]=255;palette=palette.tobytes()
  else:palette=(Path(r'C:\NFSUG-Workspace\NFSUG-pc-background-tests\references')/(name.split('-')[0]+'.palette.rgba')).read_bytes()
  try:
   targets=[(240,160,240,160,0,160)]
   if name in ('11878-0-1','12137-0-0','synthetic-near'):targets.append((3840,2160,3240,2160,0,160))
   if name=='11878-0-1':targets.extend([(240,160,240,160,80,120),(240,160,240,160,80,80)])
   for w,h,aw,ah,top,bottom in targets:
    output=(C.c_ubyte*(w*h*4))();assert draw(ctx,mesh,palette,len(palette),w,h,aw,ah,top,bottom,output,len(output)),err();actual=np.frombuffer(output,np.uint8).reshape(h,w,4);expected=cpu(name,m,palette,w,h,aw,ah,top,bottom)
    diff=np.any(actual!=expected,axis=2);coverage=(actual[:,:,3]!=expected[:,:,3]);color=diff&~coverage
    row=dict(covered_pixels=int(np.count_nonzero(actual[:,:,3])),model=name,width=w,height=h,owner_top=top,owner_bottom=bottom,pixels=w*h,mismatched_pixels=int(diff.sum()),coverage_mismatches=int(coverage.sum()),color_mismatches=int(color.sum()),sha256=hashlib.sha256(output).hexdigest());row['first_differences']=[dict(x=int(x),y=int(y),actual=actual[y,x].tolist(),expected=expected[y,x].tolist()) for y,x in np.argwhere(diff)[:8]];results.append(row)
    assert not actual[:h-ah].any() and not actual[h-ah:,aw:].any(),'Inactive target modified'
    if w==3840 and name=='11878-0-1':Image.fromarray(actual[::-1].copy()).save(out/'source-model-4k.png')
    if bottom==top:assert not actual.any(),'Empty owner clip modified'
   if not guard:
    sentinel=C.create_string_buffer(b'unchanged');args=[ctx,mesh,palette,len(palette),240,160,240,160,0,160,sentinel,8];assert not draw(*args) and sentinel.raw.startswith(b'unchanged');wrong=[];thread_output=(C.c_ubyte*153600)();thread_args=args[:-2]+[thread_output,153600];thread=threading.Thread(target=lambda:wrong.append(draw(*thread_args)));thread.start();thread.join();assert wrong==[0];guard=True
   if held:free(held)
   held=mesh;mesh=None
  finally:
   if mesh:free(mesh)
finally:close(ctx)
# A mesh and palette can be rendered after the first GL context has been destroyed.
recreated=[]
def recreate():
 c=op()
 try:
  assert c,err();buf=(C.c_ubyte*153600)();assert draw(c,held,palette,len(palette),240,160,240,160,0,160,buf,len(buf)),err();assert not any(buf);recreated.append(True)
 finally:
  if c:close(c)
t=threading.Thread(target=recreate);t.start();t.join();free(held);assert recreated==[True]
# Exact material contract cases: a full source rectangle avoids uncertain slanted-edge raster rules.
def rectangle(rgba,index=None):
 raw=bytearray(370);struct.pack_into('<6I',raw,0,0x324d464e,4,2,6,1,1);struct.pack_into('<3d',raw,24,120,80,64);struct.pack_into('<d',raw,96,1);struct.pack_into('<d',raw,152,1)
 for i,point in enumerate([(-120,-80,64),(-120,80,64),(120,-80,64),(120,80,64)]):struct.pack_into('<3d',raw,160+i*24,*point)
 raw[256:258]=bytes([3,3]);struct.pack_into('<6H',raw,258,0,1,2,2,1,3)
 for i in range(6):struct.pack_into('<2d',raw,270+i*16,.25,.25)
 raw[366:370]=bytes(rgba)
 if index is not None:raw+=struct.pack('<4I',0x31495a4e,1,1,0)+bytes([index])
 return bytes(raw)
material_cases=[];ctx=op();assert ctx,err()
try:
 pal=np.zeros((160,256,4),np.uint8);pal[:,:,0]=np.arange(256,dtype=np.uint8)[None,:];pal[:,:,1]=np.arange(160,dtype=np.uint8)[:,None];pal[:,:,2]=77;pal[:,:,3]=255;palette=pal.tobytes()
 for label,rgba,index in [('opaque-rgba',(21,42,63,255),None),('transparent-rgba-uses-zero',(21,42,63,0),None),('opaque-index-zero',(99,88,77,0),0),('indexed-173',(99,88,77,0),173)]:
  raw=rectangle(rgba,index);mesh=decode(raw,len(raw),32*1024*1024);assert mesh,label
  try:
   for w,h,aw,ah,top,bottom in [(240,160,240,160,0,160),(3840,2160,3240,2160,53,107)]:
    output=(C.c_ubyte*(w*h*4))();assert draw(ctx,mesh,palette,len(palette),w,h,aw,ah,top,bottom,output,len(output)),err();actual=np.frombuffer(output,np.uint8).reshape(h,w,4);expected=np.zeros_like(actual)
    ys=np.arange(ah);source_y=((ah-ys)*2-1)*80//ah;valid=(source_y>=top)&(source_y<bottom)
    color=np.broadcast_to(np.array(rgba,np.uint8),(ah,4)).copy() if index is None and rgba[3]>=128 else pal[source_y,index if index is not None else 0].copy();color[:,3]=255
    expected[np.where(valid)[0],:aw]=color[valid,None,:];assert np.array_equal(actual,expected),(label,w,'Exact material pixels differ')
    material_cases.append(dict(case=label,width=w,height=h,pixels=w*h,exact=True))
  finally:free(mesh)
finally:close(ctx)
report=dict(result='PC_MODEL_GPU_DIAGNOSTIC',exact_material_cases=material_cases,exact_material_pixels=sum(c['pixels'] for c in material_cases),renderer=gpu,models=32,targets=len(results),pixel_comparisons=sum(r['pixels'] for r in results),mismatched_pixels=sum(r['mismatched_pixels'] for r in results),coverage_mismatches=sum(r['coverage_mismatches'] for r in results),color_mismatches=sum(r['color_mismatches'] for r in results),short_output_wrong_thread_empty_clip_guards=True,context_recreated_on_different_thread=True,full_scene=False,full_scene_60fps=False,playable_native_release=False,reference='Independent Python rasterization of established Java mesh/plane/material exports; exact per-pixel differences recorded without tolerance.',frames=results,source_sha256={n:sha(root/'work/pc'/n) for n in ['source_frame.c','source_frame.h','model_mesh.c','model_mesh.h','model_gpu.c','model_gpu.h']},test_sha256=sha(Path(__file__)),dll_sha256=sha(out/'model-gpu.dll'))
(out/'model-gpu-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('frames','source_sha256')},indent=2))
