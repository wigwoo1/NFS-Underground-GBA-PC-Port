from pathlib import Path
import ctypes as C,struct,json,hashlib,os
from gles_model_reference import GLESModelReference
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-model-tests')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'model-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;I=C.c_int
def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn('nf_pc_model_gpu_open',[],P);close=fn('nf_pc_model_gpu_close',[P],None);decode=fn('nf_pc_model_mesh_decode',[P,S,S],P);free=fn('nf_pc_model_mesh_free',[P],None);draw=fn('nf_pc_model_gpu_draw',[P,P,P,S,U,U,U,U,U,U,P,S]);buffer=fn('nf_pc_model_mesh_buffer',[P,U,C.POINTER(P),C.POINTER(S)]);plane=fn('nf_pc_model_mesh_plane',[P,U,P])
ref=GLESModelReference(root/'work/android/java/org/codex/nfsugpreview/NativeSceneGpu.java');ctx=op();assert ctx;results=[]
try:
 for delta in [-.004,-.003,-.0021,-.0019,-.001,-.0001,0,.0001,.001,.003,.004]:
  raw=bytearray(1390);struct.pack_into('<6I',raw,0,0x324d464e,4,2,6,256,1);struct.pack_into('<3d',raw,24,120,80,64);struct.pack_into('<d',raw,96,1);struct.pack_into('<d',raw,152,1)
  for i,point in enumerate([(-120,-80,64),(-120,80,64),(120,-80,64),(120,80,64)]):struct.pack_into('<3d',raw,160+i*24,*point)
  raw[256:258]=bytes([3,3]);struct.pack_into('<6H',raw,258,0,1,2,2,1,3)
  for i in range(6):struct.pack_into('<2d',raw,270+i*16,(1+delta)/256,.5)
  tex=b''.join(bytes([i,100,200,255]) for i in range(256));raw[366:]=tex;raw=bytes(raw);mesh=decode(raw,len(raw),32*1024*1024);assert mesh
  try:
   ptr=P();n=S();assert buffer(mesh,0,C.byref(ptr),C.byref(n));vertices=C.string_at(ptr,n.value);planes=[]
   for tri in range(2):p=(C.c_float*11)();assert plane(mesh,tri,p);planes.append(bytes(p))
   palette=bytes(163840);output=(C.c_ubyte*1024)();assert draw(ctx,mesh,palette,len(palette),16,16,16,16,0,160,output,len(output));reference=ref.render(vertices,b''.join(planes),tex,b'',palette,256,1,16,16,16,16,0,160)
   a=bytes(output);at=(8*16+8)*4;results.append(dict(offset_from_texel_boundary=delta,native=list(a[at:at+4]),gles=list(reference[at:at+4]),full_rectangle_exact=a==reference))
  finally:free(mesh)
finally:close(ctx);ref.close()
r=dict(result='PC_TEXTURE_NEAREST_BOUNDARY_DIAGNOSTIC',cases=results,production_changed=False,full_scene=False,test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(out/'model-nearest-boundary-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
