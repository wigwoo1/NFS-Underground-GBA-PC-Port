from pathlib import Path
import ctypes as C,struct,io,json,hashlib,os
source=Path(__file__).parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-mesh-tests')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'world-mesh.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int

def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
read=fn('nf_pc_world_decode',[P,S,S],P);world_free=fn('nf_pc_world_free',[P],None);wi=fn('nf_pc_world_info',[P,P]);make=fn('nf_pc_world_mesh',[P,U,S],P);free=fn('nf_pc_world_mesh_free',[P],None);info=fn('nf_pc_world_mesh_info',[P,P]);buf=fn('nf_pc_world_mesh_buffer',[P,U,C.POINTER(P),C.POINTER(S)]);plane=fn('nf_pc_world_mesh_plane',[P,U,P]);model=fn('nf_pc_world_model',[P,U,C.POINTER(P),C.POINTER(S)])
def blob(mesh,kind):p=P();n=S();assert buf(mesh,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
worlds=surfaces=vertices=plane_count=camera_values=0;peak=0;modes={};synthetic={}
for path in sorted((out/'inputs').glob('*.nsp')):
 stream=io.BytesIO((out/'references'/path.with_suffix('.mesh').name).read_bytes())
 def integer():return struct.unpack('>I',stream.read(4))[0]
 raw=path.read_bytes();w=read(raw,len(raw),64*1024*1024);assert w,path.name;count=integer();meta=(Q*4)();assert wi(w,meta) and meta[0]==count;held=None;held_bytes=None;held_planes=None
 try:
  p=P();n=S();assert model(w,0,C.byref(p),C.byref(n));model0=C.string_at(p,n.value);offset,size=struct.unpack_from('<2I',raw,36)
  section=raw[offset:offset+size]
  if meta[1]==1:assert model0==section
  else:
   offset,size=struct.unpack_from('<2I',section,8);assert model0==section[offset:offset+size]
  assert not model(w,meta[1],C.byref(p),C.byref(n))
  for i in range(count):
   affine=integer();source_camera=integer();nc=integer();camera=stream.read(nc*8);nf=integer();floats=stream.read(nf*4);np=integer();planes=stream.read(np*44)
   mesh=make(w,i,32*1024*1024);assert mesh,(path.name,i,'rejected');m=(Q*16)();assert info(mesh,m) and m[12]*5==nf and m[13]==affine and m[14]==source_camera
   assert blob(mesh,0)==floats,(path.name,i,'vertices');assert blob(mesh,1)==camera,(path.name,i,'camera');actual=[]
   for j in range(np):v=(C.c_float*11)();assert plane(mesh,j,v);actual.append(bytes(v))
   assert b''.join(actual)==planes,(path.name,i,'planes');peak=max(peak,m[15]);modes[str(m[4])]=modes.get(str(m[4]),0)+1;surfaces+=1;vertices+=nf//5;camera_values+=nc;plane_count+=np
   assert not make(w,i,m[15]-1);exact=make(w,i,m[15]);assert exact;free(exact);v=(C.c_float*11)(*[77]*11);assert not plane(mesh,np,v) and list(v)==[77]*11
   if path.name.startswith('synthetic'):synthetic[path.stem]=nf//5
   if held:free(held)
   held=mesh;held_bytes=[floats,camera];held_planes=planes
  assert not stream.read() and not make(w,count,32*1024*1024)
 finally:world_free(w)
 assert [blob(held,k) for k in range(2)]==held_bytes
 actual=[]
 for j in range(len(held_planes)//44):v=(C.c_float*11)();assert plane(held,j,v);actual.append(bytes(v))
 assert b''.join(actual)==held_planes;free(held);worlds+=1
assert synthetic['synthetic-concave-degenerate']==6
assert worlds==34 and surfaces==405 and synthetic['synthetic-hidden']==0 and synthetic['synthetic-collinear']==0 and synthetic['synthetic-concave']==9 and synthetic['synthetic-concave-reverse']==9
# Valid world containers with unsupported/inconsistent model-camera state reject atomically.
faults=[]
base=(out/'inputs/synthetic-mode-0.nsp').read_bytes();model_at=struct.unpack_from('<I',base,36)[0]
for at,value in [(model_at+24,float('nan')),(model_at+40,0),(model_at+96,0)]:
 raw=bytearray(base);struct.pack_into('<d',raw,at,value);faults.append(bytes(raw))
for mode in [5,9]:
 raw=bytearray((out/f'inputs/synthetic-mode-{mode}.nsp').read_bytes());at,size=struct.unpack_from('<2I',raw,72);raw[at+size-131072:at+size]=bytes(131072);faults.append(bytes(raw))
base=(out/'inputs/synthetic-mode-9.nsp').read_bytes();model_at=struct.unpack_from('<I',base,36)[0];raw=bytearray(base);struct.pack_into('<d',raw,model_at+24,120.5);faults.append(bytes(raw));raw=bytearray(base);at=struct.unpack_from('<I',raw,84)[0];struct.pack_into('<d',raw,at+8+40+8,.5);faults.append(bytes(raw))
base=(out/'inputs/11878-0.nsp').read_bytes();model_at=struct.unpack_from('<I',base,36)[0];raw=bytearray(base);second=struct.unpack_from('<I',raw,model_at+16)[0];struct.pack_into('<d',raw,model_at+second+24,999);faults.append(bytes(raw));raw=bytearray(base);struct.pack_into('<I',raw,model_at+8,1);faults.append(bytes(raw))
for raw in faults:
 w=read(raw,len(raw),64*1024*1024);assert w,'Fault must remain a valid world container'
 try:assert not make(w,0,32*1024*1024),'Inconsistent model-camera mesh accepted'
 finally:world_free(w)
r=dict(result='PASS_PC_WORLD_MESH',worlds=worlds,actual_source_owners=17,actual_surfaces=388,synthetic_surfaces=17,surfaces=surfaces,triangle_vertices=vertices,camera_double_values=camera_values,texture_planes=plane_count,modes=modes,synthetic_triangle_vertices=synthetic,maximum_requested_bytes=peak,world_free_lifetime_verified=True,inconsistent_camera_cases_rejected=len(faults),exact_and_short_budget_verified=True,original_model_view_verified=True,camera_mesh_planes_byte_identical_to_java=True,source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['source_frame.c','source_frame.h','source_world.c','source_world.h','source_road.c','source_road.h','world_mesh.c','world_mesh.h']},test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/'world-mesh.dll').read_bytes()).hexdigest(),gpu_world_drawing=False,full_scene=False,full_scene_60fps=False)
(out/'world-mesh-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
