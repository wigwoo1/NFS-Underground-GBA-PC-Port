from pathlib import Path
import ctypes as C,hashlib,json,os,struct,math
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-pc-empty-plane-second-failure';r=json.loads((folder/'second-failure-report.json').read_text());detail=r['detail'];owner,index=detail[16],detail[18]
blob=(folder/f'witness-owner{owner}-kind1.bin').read_bytes();at,n=struct.unpack_from('<II',blob,36);models=blob[at:at+n]
if struct.unpack_from('<I',models)[0]==0x314c4d4e:at,n=struct.unpack_from('<II',models,8+index*8);model=models[at:at+n]
else:assert index==0;model=models
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64
def fn(n,args,result=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
owned=C.create_string_buffer(model);mesh=fn('nf_pc_model_mesh_decode',[P,S,S],P)(owned,len(model),32*1024*1024);assert mesh
try:
 info=(Q*12)();assert fn('nf_pc_model_mesh_info',[P,P])(mesh,info);ptr=P();size=S();assert fn('nf_pc_model_mesh_buffer',[P,U,P,P])(mesh,0,C.byref(ptr),C.byref(size));vertices=C.string_at(ptr,size.value);(folder/'model-vertices.bin').write_bytes(vertices);values=struct.unpack('<%df'%(len(vertices)//4),vertices);failed=[]
 for i in range(info[4]//3):
  plane=(C.c_float*11)()
  if not fn('nf_pc_model_mesh_plane',[P,U,P])(mesh,i,plane):
   v=values[i*15:(i+1)*15];fallback=bool(fn('nf_pc_test_empty_plane',[P,P])((C.c_float*15)(*v),plane));failed.append(dict(triangle=i,vertices=list(v),axis_fallback=fallback,det=(v[5]-v[0])*(v[11]-v[1])-(v[6]-v[1])*(v[10]-v[0]),all_finite=all(math.isfinite(x) for x in v)))
finally:fn('nf_pc_model_mesh_free',[P],None)(mesh)
report=dict(result='INSPECTED_SECOND_MODEL_PLANE_FAILURE',logic_step=3800,source_detail=detail,owner=owner,model=index,model_info=list(info),failed_planes=failed,effective_clip=[detail[25],detail[26],max(detail[27],detail[29]),min(detail[28],detail[30])],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(folder/'second-plane-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
