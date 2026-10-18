"""Saved-scene recovery plus actual filled-triangle GPU noncoverage controls."""
from pathlib import Path
import ctypes as C,hashlib,io,json,os,runpy,contextlib,math,struct,sys
import numpy as np
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-empty-model-plane-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();b=json.loads((out/'empty-plane-build-report.json').read_text())
assert b['dll_sha256']==sha(out/'source-scene-empty-plane.dll') and b['helper_sha256']==sha(source/'empty_model_plane.h')
saved_argv=sys.argv;sys.argv=[str(source/'replay_scene_prepare_witness.py'),'--baseline-dll',str(out/'before/source-scene.dll')]
try:
 with contextlib.redirect_stdout(io.StringIO()):env=runpy.run_path(str(source/'replay_scene_prepare_witness.py'))
finally:sys.argv=saved_argv
P=env['P'];S=env['S'];Q=env['Q'];U=env['U'];fn=env['fn'];d=env['d'];api=env['api'];metadata=env['metadata']
with os.add_dll_directory('C:/msys64/mingw64/bin'):candidate=C.CDLL(str(out/'source-scene-empty-plane.dll'))
frame=fn(d,'nf_pc_source_frame_capture',[P,S],P)(C.byref(api),64*1024*1024);assert frame
F15=C.c_float*15;F11=C.c_float*11;empty=fn(candidate,'nf_pc_test_empty_plane',[P,P]);checks=0
v=[50,87,0,0,1,100,87,1,0,1,150,87,1,1,1]
for xy in [[50,87,100,87,150,87],[100,40,100,80,100,120],[100,87]*3,[50,40,150,120,50,40]]:
 data=v.copy()
 for i in range(3):data[i*5:i*5+2]=xy[i*2:i*2+2]
 plane=F11();assert empty(F15(*data),plane) and all(math.isfinite(x) for x in plane) and list(plane)[4]==1 and list(plane)[5:]==[0]*6;checks+=1
badcases=[]
x=v.copy();x[6]=87.0001;badcases.append(x)
x=v.copy();x[4]=0;badcases.append(x)
x=v.copy();x[9]=-1;badcases.append(x)
x=v.copy();x[1]=float('nan');badcases.append(x)
x=v.copy();x[14]=float('inf');badcases.append(x)
x=v.copy();x[1]=0;x[6]=1;x[11]=2;badcases.append(x) # Non-axis collinear stays unsupported.
x=v.copy();x[2]=3e38;x[4]=1e-40;badcases.append(x)
for data in badcases:
 sentinel=F11(*([123.25]*11));assert not empty(F15(*data),sentinel) and list(sentinel)==[123.25]*11;checks+=1
sentinel=F11(*([123.25]*11));assert not empty(None,sentinel) and list(sentinel)==[123.25]*11 and not empty(F15(*v),None);checks+=2
scene=fn(candidate,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024);assert scene,'Candidate did not recover saved scene'
try:
 inf=(Q*8)();assert fn(candidate,'nf_pc_scene_info',[P,P])(scene,inf);commands=[];target=None
 for i in range(inf[3]):
  ci=(Q*16)();assert fn(candidate,'nf_pc_scene_command_info',[P,U,P])(scene,i,ci);commands.append(list(ci))
  if list(ci)[:3]==[1,1,2]:target=i
 assert target is not None
 ptr=P();n=S();assert fn(candidate,'nf_pc_scene_command_buffer',[P,U,U,P,P])(scene,target,0,C.byref(ptr),C.byref(n));vertices=C.string_at(ptr,n.value)
 fixture=base/'NFSUG-pc-scene-prepare-failure-replay';assert vertices==(fixture/'failing-model-vertices.bin').read_bytes()
 assert fn(candidate,'nf_pc_scene_command_buffer',[P,U,U,P,P])(scene,target,1,C.byref(ptr),C.byref(n));planes=C.string_at(ptr,n.value);assert len(planes)==42*44
 mesh=fn(d,'nf_pc_source_model_mesh',[P,U,U,S],P)(frame,1,2,32*1024*1024);assert mesh
 try:
  valid_planes=0;strict=fn(d,'nf_pc_model_mesh_plane',[P,U,P])
  for i in range(42):
   plane=F11(*([123.25]*11));ok=strict(mesh,i,plane)
   if i in [20,21]:
    assert not ok and list(plane)==[123.25]*11
    actual=struct.unpack_from('<11f',planes,i*44);assert actual[4]==1 and actual[5:]==(0,)*6 and all(math.isfinite(x) for x in actual)
   else:assert ok and bytes(plane)==planes[i*44:(i+1)*44];valid_planes+=1
  assert valid_planes==40
 finally:fn(d,'nf_pc_model_mesh_free',[P],None)(mesh)
 gpu=fn(candidate,'nf_pc_scene_gpu_open',[],P)();assert gpu
 try:
  testgpu=fn(candidate,'nf_pc_test_triangle_gpu',[P,P,P,U,U,U,U,P,S]);draw=fn(candidate,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);results=[]
  cases={'point':[100,87]*3,'horizontal':[50,87,100,87,150,87],'vertical':[100,40,100,80,100,120],'repeated':[50,40,150,120,50,40],'thin':[50,87.25,150,87.25,100,87.75],'visible':[50,40,150,40,100,120]}
  for w,h,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
   baseline=None
   for name,xy in cases.items():
    pixels=C.create_string_buffer(w*h*4);assert testgpu(gpu,scene,(C.c_float*6)(*xy),w,h,aw,ah,pixels,len(pixels));raw=pixels.raw;array=np.frombuffer(raw,np.uint8).reshape(h,w,4);red=int(np.count_nonzero((array[:,:,0]==255)&(array[:,:,1]==0)&(array[:,:,2]==0)))
    if name=='point':baseline=raw;assert red==0
    elif name in ['horizontal','vertical','repeated']:assert red==0 and raw==baseline
    else:assert red>0
    results.append(dict(size=[w,h],case=name,red_pixels=red,sha256=hashlib.sha256(raw).hexdigest()))
   pixels=C.create_string_buffer(w*h*4);assert draw(gpu,scene,w,h,aw,ah,pixels,len(pixels));(out/f'recovered-scene-{w}.rgba').write_bytes(pixels.raw)
 finally:fn(candidate,'nf_pc_scene_gpu_close',[P],None)(gpu)
finally:fn(candidate,'nf_pc_scene_free',[P],None)(scene);fn(d,'nf_pc_source_frame_free',[P],None)(frame)
report=dict(result='PASS_EMPTY_AXIS_MODEL_PLANE_SAVED_FRAME_AND_GPU',helper_cases=checks,malformed_and_nonaxis_atomic_rejection=True,saved_scene_prepares=True,source_vertices_and_command_order_preserved=True,valid_plane_bytes_exact=40,placeholder_planes=[20,21],strict_model_plane_api_still_rejects_degenerate=True,actual_gpu_horizontal_vertical_repeated_zero_coverage=True,actual_gpu_thin_and_visible_triangles_draw=True,gpu_cases=results,prepared_info=list(inf),command_info=commands,helper_sha256=sha(source/'empty_model_plane.h'),build_receipt_sha256=sha(out/'empty-plane-build-report.json'),script_sha256=sha(Path(__file__)),full_scene_60fps=False,scope='Local AMD GPU and the saved failure. No complete route or original-image fidelity claim yet.')
(out/'empty-plane-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='command_info'},indent=2))
