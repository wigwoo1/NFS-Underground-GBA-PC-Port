"""Replay the saved owner-bound frame without ROM/core execution; isolate model planes."""
from pathlib import Path
import ctypes as C,hashlib,json,math,os,struct,argparse
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-pc-scene-prepare-failure-replay';diagdir=base/'NFSUG-pc-scene-prepare-failure-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,default=folder);parser.add_argument('--probe-dir',type=Path,default=diagdir);parser.add_argument('--baseline-dll',type=Path,default=base/'NFSUG-pc-scene-tests/source-scene.dll');args=parser.parse_args();folder=args.folder;diagdir=args.probe_dir;baseline_dll=args.baseline_dll
r=json.loads((folder/'diverse-route-report.json').read_text());w=json.loads((folder/'witness-components.json').read_text());assert r['steps']==3593 and r['prepare_failures'][0]['detail'][0]==18
blobs={};owners={}
for row in w:
 path=folder/Path(row['file']).name;assert sha(path)==row['sha256'] and path.stat().st_size==row['bytes'];blobs[row['owner'],row['kind']]=path.read_bytes();owners[row['owner']]=row['owner_info']
metadata=r['prepare_failures'][0]['frame_info'];P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
dll_dirs=[os.add_dll_directory(str(path)) for path in [folder,baseline_dll.parent,Path('C:/msys64/mingw64/bin')] if path.is_dir()]
d=C.CDLL(str(baseline_dll));dd=C.CDLL(str(diagdir/'source-scene-failure.dll'))
factory=json.loads((diagdir/'scene-prepare-probe-build-report.json').read_text());assert factory['dll_sha256']==sha(diagdir/'source-scene-failure.dll') and factory['baseline_dll_sha256']==sha(baseline_dll)
Info=C.CFUNCTYPE(I,P,P);Background=C.CFUNCTYPE(S,P,Q,U,P,S);Read=C.CFUNCTYPE(S,P,Q,U,U,U,P,S)
@Info
def info(core,out):
 data=(Q*5)(metadata[0],metadata[1],0,0,0);C.memmove(out,data,40);return 1

def copy(data,out,n):
 if not out:return len(data)
 if n<len(data):return 0
 C.memmove(out,data,len(data));return len(data)
@Background
def background(core,epoch,refresh,out,n):return copy(blobs[0,0],out,n) if [epoch,refresh]==metadata[:2] else 0
callbacks=[]
for kind in range(1,5):
 def reader(core,epoch,serial,begin,end,out,n,kind=kind):
  for owner,identity in owners.items():
   if [epoch,serial,begin,end]==identity[:4]:return copy(blobs[owner,kind],out,n)
  return 0
 callbacks.append(Read(reader))
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,result=I):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
api=API(C.sizeof(API),1,C.cast(info,P),C.cast(background,P),*[C.cast(x,P) for x in callbacks],0);assert fn(d,'nf_pc_source_api_bind_owner',[P])(C.byref(api))
frame=fn(d,'nf_pc_source_frame_capture',[P,S],P)(C.byref(api),64*1024*1024);assert frame
try:
 actual=(Q*8)();assert fn(d,'nf_pc_source_frame_info',[P,P])(frame,actual) and list(actual)==metadata
 assert not fn(d,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024)
 assert not fn(dd,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024)
 detail=(Q*32)();assert fn(dd,'nf_pc_scene_failure_detail',[P])(detail) and list(detail)==r['prepare_failures'][0]['detail']
 owner,index=detail[16],detail[18];assert owner==1 and index==2 and detail[17]==1
 mesh=fn(d,'nf_pc_source_model_mesh',[P,U,U,S],P)(frame,owner,index,32*1024*1024);assert mesh
 try:
  mi=(Q*12)();assert fn(d,'nf_pc_model_mesh_info',[P,P])(mesh,mi);ptr=P();nb=S();assert fn(d,'nf_pc_model_mesh_buffer',[P,U,P,P])(mesh,0,C.byref(ptr),C.byref(nb))
  data=C.string_at(ptr,nb.value);assert nb.value==mi[4]*20;vertices=struct.unpack('<%df'%(nb.value//4),data);(folder/'failing-model-vertices.bin').write_bytes(data)
  failed=[];plane_fn=fn(d,'nf_pc_model_mesh_plane',[P,U,P])
  for triangle in range(mi[4]//3):
   plane=(C.c_float*11)(*([123.25]*11));ok=plane_fn(mesh,triangle,plane)
   if not ok:
    assert list(plane)==[123.25]*11
    v=list(vertices[triangle*15:(triangle+1)*15]);bx=v[5]-v[0];by=v[6]-v[1];cx=v[10]-v[0];cy=v[11]-v[1];det=bx*cy-by*cx
    failed.append(dict(triangle=triangle,vertices=v,determinant=det,first_inverse_depth=v[4],all_values_finite=all(math.isfinite(x) for x in v)))
  assert failed and all(x['determinant']==0 and x['first_inverse_depth']>0 and x['all_values_finite'] for x in failed)
 finally:fn(d,'nf_pc_model_mesh_free',[P],None)(mesh)
finally:fn(d,'nf_pc_source_frame_free',[P],None)(frame)
result=dict(result='VERIFIED_FROZEN_FRAME_DEGENERATE_MODEL_PLANE_REJECTION',logic_step=3593,epoch=metadata[0],refresh=metadata[1],owner=owner,model_index=index,model_info=list(mi),triangle_count=mi[4]//3,failed_planes=failed,unchanged_and_diagnostic_scene_reject_identically=True,source_frame_rebuilt_through_checked_public_api=True,no_emulator_or_rom_access=True,plane_rejection_atomic=True,scene_retained_bytes_before_failure=detail[7],source_scene_maximum_bytes=64*1024*1024,full_scene_60fps=False,script_sha256=sha(Path(__file__)),witness_manifest_sha256=sha(folder/'witness-components.json'),replay_receipt_sha256=sha(folder/'diverse-route-report.json'),scene_probe_receipt_sha256=sha(diagdir/'scene-prepare-probe-build-report.json'),vertices_sha256=sha(folder/'failing-model-vertices.bin'),limits='First CPU scene-preparation failure only, not all163 failures. Degenerate projected triangles need correct handling under original visibility/order/texture semantics; no triangle omission or runtime fix is implemented.')
(folder/'frozen-frame-plane-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
