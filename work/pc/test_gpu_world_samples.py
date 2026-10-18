from pathlib import Path
import hashlib,subprocess,os,json
base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-world-gpu-sample-tests';root=Path('Y:/CODEX/NFSUG-Native-PC-Port')
verified=json.loads((base/'NFSUG-pc-world-source-class-tests/class-test-report.json').read_text())['test_sha256']
paths=[p for p in (base/'NFSUG-pc-world-source-class-tests').glob('class-real-*.py') if hashlib.sha256(p.read_bytes()).hexdigest()==verified];assert len(paths)==1
text=paths[0].read_text().replace('NFSUG-pc-world-source-class-tests','NFSUG-pc-world-gpu-sample-tests').replace('world-source-classes.dll','world-gpu-samples.dll')
extra=r'''
from PIL import Image,ImageChops
import math
gpu_open=fn(d,'nf_pc_scene_gpu_open',[],P);gpu_close=fn(d,'nf_pc_scene_gpu_close',[P],None)
gpu_draw=fn(d,'nf_pc_scene_gpu_draw_passes',[P,P,U,U,U,U,U,P,S]);gpu_samples=fn(d,'nf_pc_scene_gpu_draw_world_meshes',[P,P,P,S,U,U,U,U,U,P,S]);gpu_error=fn(d,'nf_pc_scene_gpu_error',[],C.c_char_p)
gpu=gpu_open();assert gpu,gpu_error();gpu_counts=Counter();gpu_kinds=set();gpu_results=[]
def gpu_batch_check(scene,commands,role,batch,zero):
 if gpu_counts['owner_batches']:return
 si=(Q*8)();assert sinfo(scene,si);slots=(P*si[3])();zeros=(P*si[3])();held=[]
 try:
  for j,(meta,owner_key,source_id) in enumerate(commands):
   if meta[0]!=role or meta[1]:continue
   m=class_mesh(batch,meta[2],32*1024*1024)
   if not m:continue
   held.append(m);z=class_mesh(zero,meta[2],32*1024*1024);assert z;held.append(z);slots[j]=m;zeros[j]=z
   gpu_counts['batch_world_commands']+=1
   if meta[8]:gpu_counts['batch_lit_commands']+=1
  assert held
  n=3840*2160*4;a=(C.c_ubyte*n)();b=(C.c_ubyte*n)()
  assert gpu_draw(gpu,scene,3840,2160,3240,2160,15,a,n)
  assert gpu_samples(gpu,scene,zeros,si[3],3840,2160,3240,2160,15,b,n) and bytes(a)==bytes(b)
  gpu_counts['exact_4k_endpoint_pixels']+=3840*2160
  assert gpu_samples(gpu,scene,slots,si[3],3840,2160,3240,2160,15,b,n) and bytes(a)!=bytes(b)
  gpu_counts['owner_batches']+=1
 finally:
  for m in held:mesh_free(m)
def gpu_check(scene,index,zero,middle,kind):
 if kind in gpu_kinds or gpu_counts['attempts']>=16:return
 gpu_counts['attempts']+=1
 si=(Q*8)();meta=(Q*16)();assert sinfo(scene,si) and command_info(scene,index,meta)
 slots=(P*si[3])();n=3840*2160*4;a=(C.c_ubyte*n)();b=(C.c_ubyte*n)();c=(C.c_ubyte*n)()
 assert gpu_draw(gpu,scene,3840,2160,3240,2160,15,a,n),gpu_error()
 slots[index]=zero;assert gpu_samples(gpu,scene,slots,si[3],3840,2160,3240,2160,15,b,n),gpu_error()
 assert bytes(a)==bytes(b),'alpha0 complete scene changed';gpu_counts['exact_4k_endpoint_pixels']+=3840*2160
 if not gpu_counts['guards']:
  sentinel=(C.c_ubyte*16)(*[173]*16)
  for array,count,passes,length in [(slots,si[3]-1,15,16),(None,si[3],15,16),(slots,si[3],16,16),(slots,si[3],15,16)]:
   assert not gpu_samples(gpu,scene,array,count,3840,2160,3240,2160,passes,sentinel,length) and list(sentinel)==[173]*16
   gpu_counts['guards']+=1
  model=next((j for j in range(si[3]) if (lambda x: command_info(scene,j,x) and x[1])((Q*16)())),None)
  if model is not None:
   wrong=(P*si[3])();wrong[model]=middle
   assert not gpu_samples(gpu,scene,wrong,si[3],3840,2160,3240,2160,15,sentinel,16) and list(sentinel)==[173]*16 and gpu_error()==b'World sample binding';gpu_counts['guards']+=1
  frozen=bytes(a)
  assert not gpu_samples(gpu,scene,slots,si[3],3840,2160,3240,2160,16,a,n) and bytes(a)==frozen
  gpu_counts['guards']+=1
 slots[index]=middle;assert gpu_samples(gpu,scene,slots,si[3],3840,2160,3240,2160,15,c,n),gpu_error()
 first=Image.frombytes('RGBA',(3840,2160),bytes(a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 image=Image.frombytes('RGBA',(3840,2160),bytes(c)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 box=ImageChops.difference(first,image).convert('RGB').getbbox()
 edge=lambda cell,extent,source:math.ceil(cell*extent/source-.5)
 expected=(edge(meta[9],3240,240),edge(max(meta[11],meta[13]),2160,160),edge(meta[10],3240,240),edge(min(meta[12],meta[14]),2160,160))
 if box:
  assert box[0]>=expected[0] and box[1]>=expected[1] and box[2]<=expected[2] and box[3]<=expected[3],(box,expected)
  gpu_kinds.add(kind);gpu_counts['visible_source_kind_'+str(kind)]+=1;gpu_counts['clipped_changed_renders']+=1
  if len(gpu_kinds)==1:image.save(out/'sampled-world-diagnostic.png')
  gpu_results.append(dict(kind=kind,command=index,source_metadata=list(meta),changed_bbox=box,allowed_scissor=expected,endpoint_sha256=hashlib.sha256(bytes(a)).hexdigest(),sample_sha256=hashlib.sha256(bytes(c)).hexdigest()))
 else:gpu_counts['occluded_or_unchanged']+=1
 assert gpu_draw(gpu,scene,3840,2160,3240,2160,15,b,n) and bytes(a)==bytes(b),'parent scene changed by borrowed view'
 gpu_counts['parent_scene_unchanged']+=1
'''
marker='class_counts=Counter();kept_mesh=None;class_seen=set()';assert text.count(marker)==1;text=text.replace(marker,marker+'\n'+extra)
marker='try:assert blob(mesh_buffer,z,0)==blob(scene_vertices,old,oi,0)';assert text.count(marker)==1;text=text.replace(marker,'try:\n       assert blob(mesh_buffer,z,0)==blob(scene_vertices,old,oi,0)\n       gpu_check(old,oi,z,m,kind)')
marker="oldpacket=blob(packet_view,old,ar);newpacket=blob(packet_view,new,br)";assert text.count(marker)==1;text=text.replace(marker,marker+'\n    gpu_batch_check(old,aa,ar,batch,zero)')
marker="print('CLASS_COUNTS',dict(class_counts),flush=True)";assert text.count(marker)==1
text=text.replace(marker,marker+'''\nassert gpu_kinds=={1,2},(gpu_kinds,dict(gpu_counts))
gpu_close(gpu)
(out/'gpu-sample-report.json').write_text(json.dumps(dict(result='PASS_4K_WORLD_POSE_GPU_DIAGNOSTIC',counts=dict(gpu_counts),samples=gpu_results,build_sha256=b['exe_sha256'],dll_sha256=b['identity_dll_sha256'],full_scene_60fps=False,live_enabled=False,endpoint_sky_hud_retention_held=True),indent=2))
print('GPU_COUNTS',dict(gpu_counts),flush=True)
''')
p=out/('gpu-real-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text)
r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=240);(out/'gpu-sample-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
