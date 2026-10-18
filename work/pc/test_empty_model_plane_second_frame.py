from pathlib import Path
import ctypes as C,hashlib,json,os,sys
source=Path(__file__).resolve().parent;sys.path.insert(0,str(source))
from source_frame_witness import capture_witness,function as fn,P,Q,U,S
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-pc-empty-plane-second-failure';out=base/'NFSUG-pc-empty-model-plane-tests';r=json.loads((folder/'second-failure-report.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-scene-empty-plane.dll'))
frame=capture_witness(d,folder,r['frame_info']);scene=None
try:
 scene=fn(d,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024);assert scene
 info=(Q*8)();assert fn(d,'nf_pc_scene_info',[P,P])(scene,info);target=None
 for i in range(info[3]):
  meta=(Q*16)();assert fn(d,'nf_pc_scene_command_info',[P,U,P])(scene,i,meta)
  if list(meta)[:3]==[1,1,0]:target=i
 assert target is not None
 ptr=P();n=S();assert fn(d,'nf_pc_scene_command_buffer',[P,U,U,P,P])(scene,target,0,C.byref(ptr),C.byref(n));assert C.string_at(ptr,n.value)==(folder/'model-vertices.bin').read_bytes()
 assert fn(d,'nf_pc_scene_command_buffer',[P,U,U,P,P])(scene,target,1,C.byref(ptr),C.byref(n));planes=C.cast(ptr,C.POINTER(C.c_float));assert planes[15*11+4]==1 and all(planes[15*11+i]==0 for i in range(5,11))
 result=dict(result='PASS_REPEATED_VERTEX_FULL_FRAME_RECOVERY',logic_step=3800,prepared_info=list(info),unchanged_source_vertices=True,repeated_position_triangle=15,frame_capture_via_checked_api=True,no_emulator_or_rom_access=True,helper_sha256=sha(source/'empty_model_plane.h'),dll_sha256=sha(out/'source-scene-empty-plane.dll'),script_sha256=sha(Path(__file__)),witness_loader_sha256=sha(source/'source_frame_witness.py'),full_scene_60fps=False);(out/'second-frame-test-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:
 if scene:fn(d,'nf_pc_scene_free',[P],None)(scene)
 fn(d,'nf_pc_source_frame_free',[P],None)(frame)
