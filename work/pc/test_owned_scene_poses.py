from pathlib import Path
import subprocess,os,hashlib
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-scene-pose-tests'
paths=list((base/'NFSUG-pc-scene-region-tests').glob('real-region-*.py'));assert len(paths)==1
text=paths[0].read_text().replace("out=base/'NFSUG-pc-scene-region-tests'","out=base/'NFSUG-pc-scene-pose-tests'").replace('scene-regions.dll','scene-poses.dll').replace("'nf_pc_scene_prepare'","'nf_pc_scene_prepare_motion'")
extra=r'''
default_prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);packet_view=fn(d,'nf_pc_scene_motion_packet',[P,U,P,P]);model_view=fn(d,'nf_pc_scene_motion_model',[P,U,P,P]);scene_vertices=fn(d,'nf_pc_scene_command_buffer',[P,U,U,P,P]);model_sample=fn(d,'nf_pc_scene_model_pose',[P,U,P,U,C.c_double,S],P);world_sample=fn(d,'nf_pc_scene_world_pose',[P,U,P,U,C.c_double,S],P);model_mesh_free=fn(d,'nf_pc_model_mesh_free',[P],None);world_mesh_free=fn(d,'nf_pc_world_mesh_free',[P],None);model_mesh_buffer=fn(d,'nf_pc_model_mesh_buffer',[P,U,P,P]);world_mesh_buffer=fn(d,'nf_pc_world_mesh_buffer',[P,U,P,P]);pose_counts=Counter();pose_seen=set();saved_mesh=None
gpu_open=fn(d,'nf_pc_scene_gpu_open',[],P);gpu_close=fn(d,'nf_pc_scene_gpu_close',[P],None);gpu_draw=fn(d,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);gpu=None;gpu_image=None
def buffer(f,*args):
 p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def endpoint_copy_check(frame,scene,fi):
 global gpu,gpu_image
 default=default_prepare(frame,64*1024*1024);assert default;a=(Q*8)();b=(Q*8)();assert sinfo(default,a) and sinfo(scene,b)
 assert list(a[:6])+[a[7]]==list(b[:6])+[b[7]] and b[6]>a[6]
 for role in range(fi[4]):
  original=buffer(component,frame,role,1);retained=buffer(packet_view,scene,role);assert original==retained
  pointer=P(0x1234);n=S(0x5678);assert not packet_view(default,role,C.byref(pointer),C.byref(n)) and pointer.value==0x1234 and n.value==0x5678
 for i in range(a[3]):
  assert buffer(scene_vertices,default,i,0)==buffer(scene_vertices,scene,i,0)
  assert buffer(scene_vertices,default,i,1)==buffer(scene_vertices,scene,i,1)
  for role in [default,scene]:
   metadata=(Q*16)();assert command_info(role,i,metadata)
   if metadata[1] and role==scene:assert buffer(model_view,scene,i)[:4]==b'NFM2'
 if pose_counts['endpoint_constructor_parity'] in [0,29,99,199]:
  if not gpu:gpu=gpu_open();assert gpu;gpu_image=C.create_string_buffer(3840*2160*4)
  assert gpu_draw(gpu,default,3840,2160,3240,2160,gpu_image,len(gpu_image));expected=hashlib.sha256(gpu_image).hexdigest()
  assert gpu_draw(gpu,scene,3840,2160,3240,2160,gpu_image,len(gpu_image));assert hashlib.sha256(gpu_image).hexdigest()==expected
  pose_counts['native_4k_endpoint_pixels_exact']+=3840*2160
 scene_free(default);pose_counts['endpoint_constructor_parity']+=1
 if pose_counts['endpoint_constructor_parity'] in [1,30,100,200]:
  exact=prepare(frame,b[6]);assert exact;scene_free(exact);assert not prepare(frame,b[6]-1);pose_counts['exact_budget_pairs']+=1
def check_pose(old,oi,new,ni,status,kind):
 global saved_mesh
 key=(status,kind);limit=20 if status==1 else 5
 if pose_counts['attempt_'+str(key)]>=limit:return
 # Avoid sampling the same owner/command pair twice across clipped bands.
 si=(Q*8)();assert sinfo(new,si);token=(si[1],oi,ni)
 if token in pose_seen:return
 pose_seen.add(token);pose_counts['attempt_'+str(key)]+=1
 sample,release,view=(model_sample,model_mesh_free,model_mesh_buffer) if kind==3 else (world_sample,world_mesh_free,world_mesh_buffer)
 mesh=sample(old,oi,new,ni,.5,32*1024*1024)
 if not mesh:pose_counts['unsupported_'+str(key)]+=1;return
 middle=buffer(view,mesh,0);endpoints=[]
 try:
  for alpha,s,index in [(0.,old,oi),(1.,new,ni)]:
   endpoint=sample(old,oi,new,ni,alpha,32*1024*1024);assert endpoint
   try:v=buffer(view,endpoint,0);assert v==buffer(scene_vertices,s,index,0);endpoints.append(v)
   finally:release(endpoint)
  pose_counts['sampled_'+str(key)]+=1
  if middle!=endpoints[0] and middle!=endpoints[1]:pose_counts['distinct_midpoint_'+str(kind)]+=1
  assert not sample(old,oi,new,ni,float('nan'),32*1024*1024) and not sample(old,oi,new,ni,-.1,32*1024*1024) and not sample(old,oi,new,ni,1.1,32*1024*1024) and not sample(None,oi,new,ni,.5,32*1024*1024)
  assert not sample(old,oi,new,ni,.5,0)
  if saved_mesh:saved_mesh[0](saved_mesh[2])
  saved_mesh=(release,view,mesh,middle);mesh=None
 finally:
  if mesh:release(mesh)
'''
marker='region_counts=Counter();held_region=None;held_region_snapshot=None';assert text.count(marker)==1;text=text.replace(marker,marker+'\n'+extra)
marker="region_counts['status_'+str(status)]+=1;copied_rows.append((tuple(row),tuple(ids)))";assert text.count(marker)==1;text=text.replace(marker,"region_counts['status_'+str(status)]+=1;copied_rows.append((tuple(row),tuple(ids)))\n   if a and b and status in [1,5]:check_pose(old,oi,new,ni,status,kind)")
marker='scene=prepare(frame,64*1024*1024);assert scene;si=(Q*8)();assert sinfo(scene,si);expected=[]';assert text.count(marker)==1;text=text.replace(marker,'scene=prepare(frame,64*1024*1024);assert scene;endpoint_copy_check(frame,scene,fi);si=(Q*8)();assert sinfo(scene,si);expected=[]')
anchor='   if a and b and status in [1,5]:check_pose(old,oi,new,ni,status,kind)'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"\n   if status==4 and a and pose_counts['ambiguous_rejections']<20:\n    targets=[j for j,c in enumerate(bb) if c[0][0]==newrole and c[2]==a[2]]\n    if targets:\n     sampler=model_sample if kind==3 else world_sample;assert not sampler(old,oi,new,targets[0],.5,32*1024*1024);pose_counts['ambiguous_rejections']+=1")
marker="print('REGION_COUNTS',dict(region_counts),flush=True)";assert text.count(marker)==1
addition=r'''
assert saved_mesh and pose_counts['distinct_midpoint_3']>0
assert pose_counts['native_4k_endpoint_pixels_exact']==4*3840*2160
gpu_close(gpu)
assert buffer(saved_mesh[1],saved_mesh[2],0)==saved_mesh[3];saved_mesh[0](saved_mesh[2])
(out/'pose-test-report.json').write_text(json.dumps(dict(result='PASS_OWNED_SCENE_POSE_INPUTS_AND_MESH_ENDPOINTS',counts=dict(pose_counts),source_copy_and_default_endpoint_parity=True,source_frame_scene_core_destruction_survived=True,midpoint_motion_component_only=True,build_exe_sha256=b['exe_sha256'],dll_sha256=b['identity_dll_sha256'],core_sha256=b['core_sha256'],test_sha256=sha(Path(__file__)),full_scene_60fps=False,live_motion_enabled=False),indent=2))
print('POSE_COUNTS',dict(pose_counts),flush=True)
'''
text=text.replace(marker,marker+'\n'+addition)
p=out/('owned-pose-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text)
r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=120);(out/'pose-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
