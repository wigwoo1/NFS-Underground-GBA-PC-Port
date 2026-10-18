from pathlib import Path
import ctypes as C, os, json, hashlib
import numpy as np
from gles_model_reference import GLESModelReference
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-model-tests');refs=out/'references';java=root/'work/android/java/org/codex/nfsugpreview/NativeSceneGpu.java'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'model-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;I=C.c_int
def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn('nf_pc_model_gpu_open',[],P);close=fn('nf_pc_model_gpu_close',[P],None);err=fn('nf_pc_model_gpu_error',[],C.c_char_p);decode=fn('nf_pc_model_mesh_decode',[P,S,S],P);free=fn('nf_pc_model_mesh_free',[P],None);draw=fn('nf_pc_model_gpu_draw',[P,P,P,S,U,U,U,U,U,U,P,S]);renderer=fn('nf_pc_model_gpu_renderer',[P],C.c_char_p)
ref=GLESModelReference(java);ctx=op();assert ctx,err();gpu=renderer(ctx).decode();results=[]
def classify(name,a,b,aw,ah):
 points=np.argwhere(np.any(a!=b,axis=2));tris=np.frombuffer((refs/(name+".vertices")).read_bytes(),"<f4").reshape(-1,3,5);planes=np.frombuffer((refs/(name+".planes")).read_bytes(),"<f4").reshape(-1,11);dims=next(list(map(int,line.split()[1:3])) for line in (refs/"models.txt").read_text().splitlines() if line.startswith(name+" "));coverage=[];colors=[]
 for y,x in points:
  sample=np.array([x+.5,ah-y-.5]);edge_distance=float("inf");texture_margin=float("inf")
  for tri,plane in zip(tris,planes):
   xy=tri[:,:2].astype(np.float64)*[aw/240,ah/160];edges=[]
   for v,z in zip(xy,np.roll(xy,-1,axis=0)):
    length=np.dot(z-v,z-v)
    if length:closest=v+np.clip(np.dot(sample-v,z-v)/length,0,1)*(z-v);edge_distance=min(edge_distance,float(np.linalg.norm(sample-closest)))
    edges.append(float((z[0]-v[0])*(sample[1]-v[1])-(z[1]-v[1])*(sample[0]-v[0])))
   if max(edges)<=.05:
    delta=(sample*[240/aw,160/ah]-plane[:2]).astype(np.float32);uvq=plane[2:5]+plane[5:8]*delta[0]+plane[8:11]*delta[1];texel=uvq[:2]/uvq[2]*dims;texture_margin=float(np.min(np.abs(texel-np.round(texel))))
  if a[y,x,3]!=b[y,x,3]:coverage.append(edge_distance)
  else:colors.append((edge_distance,texture_margin))
 return dict(coverage_max_edge_distance_pixels=max(coverage,default=0),color_near_edge_1_16_pixel=sum(edge<=1/16 for edge,margin in colors),color_near_texel_boundary_1_1000_texel=sum(margin<=.001 for edge,margin in colors),color_unclassified=sum(edge>1/16 and margin>.001 for edge,margin in colors),color_max_texel_boundary_distance=max((margin for edge,margin in colors if edge>1/16),default=0))

try:
 for line in (refs/'models.txt').read_text().splitlines():
  fields=line.split();name=fields[0];m=list(map(int,fields[1:]));raw=(refs/(name+'.model')).read_bytes();mesh=decode(raw,len(raw),32*1024*1024);assert mesh
  if name.startswith('synthetic'):palette=np.zeros((160,256,4),np.uint8);palette[:,:,0]=np.arange(256,dtype=np.uint8)[None,:];palette[:,:,1]=np.arange(160,dtype=np.uint8)[:,None];palette[:,:,2]=77;palette[:,:,3]=255;palette=palette.tobytes()
  else:palette=(out.parent/'NFSUG-pc-background-tests/references'/(name.split('-')[0]+'.palette.rgba')).read_bytes()
  try:
   targets=[(240,160,240,160,0,160)]
   if name in ('11878-0-1','12137-0-0','synthetic-near'):targets.append((3840,2160,3240,2160,0,160))
   if name=='11878-0-1':targets.extend([(240,160,240,160,80,120),(240,160,240,160,80,80)])
   for w,h,aw,ah,top,bottom in targets:
    output=(C.c_ubyte*(w*h*4))();assert draw(ctx,mesh,palette,len(palette),w,h,aw,ah,top,bottom,output,len(output)),err();a=np.frombuffer(output,np.uint8).reshape(h,w,4)
    expected=ref.render(*[(refs/(name+'.'+suffix)).read_bytes() for suffix in ['vertices','planes','rgba','indices']],palette,m[0],m[1],w,h,aw,ah,top,bottom);b=np.frombuffer(expected,np.uint8).reshape(h,w,4);diff=np.any(a!=b,axis=2);coverage=a[:,:,3]!=b[:,:,3]
    results.append(dict(model=name,width=w,height=h,top=top,bottom=bottom,pixels=w*h,mismatched_pixels=int(diff.sum()),coverage_mismatches=int(coverage.sum()),color_mismatches=int((diff&~coverage).sum()),covered_pixels=int(np.count_nonzero(a[:,:,3])),classification=classify(name,a,b,aw,ah),first=[dict(x=int(x),y=int(y),native=a[y,x].tolist(),gles=b[y,x].tolist()) for y,x in np.argwhere(diff)[:8]],native_sha256=hashlib.sha256(output).hexdigest(),gles_sha256=hashlib.sha256(expected).hexdigest()))
  finally:free(mesh)
finally:close(ctx);ref.close()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=dict(result='PC_MODEL_CROSS_GPU_DIAGNOSTIC',native_renderer=gpu,reference_renderer=ref.renderer,reference_version=ref.version,models=32,targets=len(results),pixel_comparisons=sum(r['pixels'] for r in results),mismatched_pixels=sum(r['mismatched_pixels'] for r in results),coverage_mismatches=sum(r['coverage_mismatches'] for r in results),color_mismatches=sum(r['color_mismatches'] for r in results),java_shader_sha256=sha(java),native_dll_sha256=sha(out/'model-gpu.dll'),reference_runtime_sha256={n:sha(ref.directory/n) for n in ['libEGL.dll','libGLESv2.dll']},test_source_sha256={n:sha(Path(__file__).parent/n) for n in ['gles_model_reference.py','test_model_cross_gpu.py']},reference_shader_unchanged=True,coverage_max_edge_distance_pixels=max(r['classification']['coverage_max_edge_distance_pixels'] for r in results),color_near_edge=sum(r['classification']['color_near_edge_1_16_pixel'] for r in results),color_near_texture_boundary=sum(r['classification']['color_near_texel_boundary_1_1000_texel'] for r in results),color_unclassified=sum(r['classification']['color_unclassified'] for r in results),color_max_texel_boundary_distance_outside_edge=max(r['classification']['color_max_texel_boundary_distance'] for r in results),full_scene=False,full_scene_60fps=False,frames=results)
(out/'model-cross-gpu-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='frames'},indent=2))
