from pathlib import Path
import json,hashlib,subprocess,os
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-owner-pose-draw-tests'
previous=base/'NFSUG-pc-world-gpu-sample-tests';verified=json.loads((previous/'identity-test-report.json').read_text())['test_sha256'];paths=[p for p in previous.glob('gpu-real-*.py') if hashlib.sha256(p.read_bytes()).hexdigest()==verified];assert len(paths)==1
text=paths[0].read_text().replace('NFSUG-pc-world-gpu-sample-tests','NFSUG-pc-owner-pose-draw-tests').replace('world-gpu-samples.dll','owner-pose-draw.dll')
extra=r'''
import numpy as np
sky_view=fn(d,'nf_pc_scene_motion_sky',[P,U,P,P]);default_prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);scene_buffer=fn(d,'nf_pc_scene_buffer',[P,U,P,P]);model_pose=fn(d,'nf_pc_scene_model_pose',[P,U,P,U,C.c_double,S],P);model_free=fn(d,'nf_pc_model_mesh_free',[P],None);model_buffer=fn(d,'nf_pc_model_mesh_buffer',[P,U,P,P]);sky_decode=fn(d,'nf_pc_sky_motion_decode',[P,S,P,P,S,P,S],P);sky_free=fn(d,'nf_pc_sky_motion_free',[P],None);sky_info=fn(d,'nf_pc_sky_motion_info',[P,P]);sky_sample=fn(d,'nf_pc_sky_motion_sample',[P,C.c_double,U,P,S,P,S,P,P]);pose_draw=fn(d,'nf_pc_scene_gpu_draw_pose_meshes',[P,P,P,P,S,P,S,U,U,U,U,U,P,S]);pose_counts=Counter();pose_results=[];last_sky=None;timing_windows=[]
def part(raw,i):
 at,n=struct.unpack_from('<2Q',raw,64+i*16);assert at<=len(raw) and n<=len(raw)-at;return raw[at:at+n]
def retained_check(frame,scene,fi):
 global last_sky
 raw=blob(component,frame,0,0);sky=part(raw,0);expected=[]
 for role in range(fi[4]):
  block=part(sky,role+1);assert len(block)==30568 and block==blob(sky_view,scene,role);expected.append(block);pose_counts['owned_sky_blocks']+=1
 last_sky=expected
 for obj,role,pp,nn in [(scene,fi[4],True,True),(None,0,True,True),(scene,0,False,True),(scene,0,True,False)]:
  p=P(0x1234);n=S(0x5678);assert not sky_view(obj,role,C.byref(p) if pp else None,C.byref(n) if nn else None) and p.value==0x1234 and n.value==0x5678;pose_counts['sky_getter_guards']+=1
 if pose_counts['constructor_checks']<4:
  si=(Q*8)();assert sinfo(scene,si);exact=prepare(frame,si[6]);assert exact;scene_free(exact);assert not prepare(frame,si[6]-1);pose_counts['exact_total_budget_pairs']+=1
  default=default_prepare(frame,64*1024*1024);assert default
  try:
   p=P(0x1234);n=S(0x5678);assert not sky_view(default,0,C.byref(p),C.byref(n)) and p.value==0x1234 and n.value==0x5678
   a=(C.c_ubyte*(3840*2160*4))();b=(C.c_ubyte*len(a))();assert gpu_draw(gpu,default,3840,2160,3240,2160,15,a,len(a)) and gpu_draw(gpu,scene,3840,2160,3240,2160,15,b,len(b)) and bytes(a)==bytes(b);pose_counts['default_motion_endpoint_pixels_exact']+=3840*2160
  finally:scene_free(default)
  pose_counts['constructor_checks']+=1
def background_at(scene,role,pair,alpha):
 lower=C.create_string_buffer(15136);upper=C.create_string_buffer(15136);weight=C.c_double();destination=U();assert sky_sample(pair,alpha,0,lower,15136,upper,15136,C.byref(weight),C.byref(destination))
 si=(Q*8)();assert sinfo(scene,si);bg=np.frombuffer(blob(scene_buffer,scene,0),dtype=np.uint8).reshape(160,240,4).copy();pal=np.frombuffer(blob(scene_buffer,scene,1),dtype=np.uint8).reshape(160,256,4)
 cells=np.arange(10560,10560+15136);y=cells//240;x=cells%240;top=0 if role==0 else si[7];bottom=160 if si[2]==1 or role==1 else si[7];mask=(y>=top)&(y<bottom)&(bg[y,x,3]!=0);at=np.nonzero(mask)[0];y=y[mask];x=x[mask];lo=np.frombuffer(lower.raw,dtype=np.uint8)[at];up=np.frombuffer(upper.raw,dtype=np.uint8)[at];q=math.floor(weight.value*65536+.5)
 bg[y,x,:3]=((pal[y,lo,:3].astype(np.uint32)*(65536-q)+pal[y,up,:3].astype(np.uint32)*q+32768)//65536).astype(np.uint8);return bg.tobytes(),weight.value
def coupled_check(old,new,aa,bb,ar,br):
 ak=next(c[1] for c in aa if c[0][0]==ar);bk=next(c[1] for c in bb if c[0][0]==br);x=blob(sky_view,old,ar);y=blob(sky_view,new,br);pair=sky_decode(x,len(x),(Q*5)(*ak),y,len(y),(Q*5)(*bk),65536)
 if not pair:pose_counts['unsupported_sky_pairs']+=1;return
 try:
  info=(Q*7)();assert sky_info(pair,info);start=max(ak[3],info[1]);end=min(bk[3],info[2]);window=dict(older_owner_end=ak[3],newer_owner_end=bk[3],older_sky_refresh=info[1],newer_sky_refresh=info[2],overlap_start=start,overlap_end=end);timing_windows.append(window)
  if start>=end:pose_counts['no_positive_shared_time_window']+=1;return
  pose_counts['shared_time_windows']+=1
  if pose_counts['coupled_4k_cases']>=2:return
  target=(start+end)/2;alpha=(target-ak[3])/(bk[3]-ak[3]);sky_alpha=(target-info[1])/(info[2]-info[1]);assert 0<alpha<1 and 0<sky_alpha<1
  batch=batch_prepare(old,ar,new,br,alpha,64*1024*1024);zero=batch_prepare(old,ar,new,br,0,64*1024*1024);assert batch and zero
  si=(Q*8)();assert sinfo(old,si);worlds=(P*si[3])();world_zeros=(P*si[3])();models=(P*si[3])();model_zeros=(P*si[3])();owned_world=[];owned_model=[]
  try:
   model_count=world_count=moving_models=0
   for j,(meta,key,identity_key) in enumerate(aa):
    if meta[0]!=ar:continue
    if not meta[1]:
     m=class_mesh(batch,meta[2],32*1024*1024)
     if not m:continue
     z=class_mesh(zero,meta[2],32*1024*1024);assert z;owned_world += [m,z];worlds[j]=m;world_zeros[j]=z;world_count+=1
    else:
     matches=[k for k,c in enumerate(bb) if c[0][0]==br and c[2]==identity_key]
     if len(matches)!=1:continue
     m=model_pose(old,j,new,matches[0],alpha,32*1024*1024)
     if not m:continue
     z=model_pose(old,j,new,matches[0],0,32*1024*1024);assert z;owned_model += [m,z];models[j]=m;model_zeros[j]=z;model_count+=1;moving_models+=int(blob(model_buffer,m,0)!=blob(model_buffer,z,0))
   if not(world_count and moving_models):pose_counts['no_moving_model_in_shared_window']+=1;return
   n=3840*2160*4;a=(C.c_ubyte*n)();b=(C.c_ubyte*n)();assert gpu_draw(gpu,old,3840,2160,3240,2160,15,a,n)
   original_bg=blob(scene_buffer,old,0);zero_bg,_=background_at(old,ar,pair,0);assert zero_bg==original_bg,'original sky endpoint/background mismatch'
   assert pose_draw(gpu,old,world_zeros,model_zeros,si[3],zero_bg,len(zero_bg),3840,2160,3240,2160,15,b,n),gpu_error();assert bytes(a)==bytes(b),'combined alpha0 changed endpoint';pose_counts['combined_endpoint_pixels_exact']+=3840*2160
   bg,weight=background_at(old,ar,pair,sky_alpha);layer_changes={}
   for label,ws,ms,bg_arg in [('world',worlds,None,None),('models',None,models,None),('sky',None,None,bg),('combined',worlds,models,bg)]:
    assert pose_draw(gpu,old,ws,ms,si[3],bg_arg,len(bg_arg) if bg_arg else 0,3840,2160,3240,2160,15,b,n),gpu_error();layer_changes[label]=hashlib.sha256(bytes(b)).hexdigest()!=hashlib.sha256(bytes(a)).hexdigest()
   if not all(layer_changes.values()):pose_counts['partially_occluded_case']+=1;return
   if not pose_counts['coupled_4k_cases']:Image.frombytes('RGBA',(3840,2160),bytes(b)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(out/'shared-owner-time-diagnostic.png')
   frozen=bytes(a)
   for bad_bg,bad_size in [(bg,153599),(None,153600)]:assert not pose_draw(gpu,old,worlds,models,si[3],bad_bg,bad_size,3840,2160,3240,2160,15,a,n) and bytes(a)==frozen;pose_counts['combined_guards']+=1
   world_index=next(i for i in range(si[3]) if worlds[i]);wrong_models=(P*si[3])();wrong_models[world_index]=owned_model[0]
   for ws in [None,worlds]:
    assert not pose_draw(gpu,old,ws,wrong_models,si[3],None,0,3840,2160,3240,2160,15,a,n) and bytes(a)==frozen
    pose_counts['combined_guards']+=1
   pose_counts['coupled_4k_cases']+=1;pose_counts['sampled_models']+=model_count;pose_counts['sampled_worlds']+=world_count;pose_results.append(dict(**window,target=target,geometry_alpha=alpha,sky_alpha=sky_alpha,sky_color_weight=weight,world_commands=world_count,model_commands=model_count,moving_models=moving_models,layer_visible_changes=layer_changes,shared_time_error=abs((ak[3]+alpha*(bk[3]-ak[3]))-(info[1]+sky_alpha*(info[2]-info[1])))))
   assert gpu_draw(gpu,old,3840,2160,3240,2160,15,b,n) and bytes(a)==bytes(b)
  finally:
   for m in owned_world:mesh_free(m)
   for m in owned_model:model_free(m)
   batch_free(batch);batch_free(zero)
 finally:sky_free(pair)
'''
marker='def gpu_batch_check(';assert text.count(marker)==1;text=text.replace(marker,extra+'\n'+marker)
marker='gpu_batch_check(old,aa,ar,batch,zero)';assert text.count(marker)==1;text=text.replace(marker,marker+'\n    coupled_check(old,new,aa,bb,ar,br)')
marker='if held:check_region(held,scene);scene_free(held)';assert text.count(marker)==1;text=text.replace(marker,'retained_check(frame,scene,fi)\n    '+marker)
marker='t.start();t.join();assert not errors;scene_free(held)';assert text.count(marker)==1;text=text.replace(marker,'t.start();t.join();assert not errors\nfor role,expected in enumerate(last_sky):assert blob(sky_view,held,role)==expected\nscene_free(held)')
marker='gpu_close(gpu)';assert text.count(marker)==1;text=text.replace(marker,"assert pose_counts['coupled_4k_cases']>=1,(dict(pose_counts),timing_windows[:4])\n(out/'owner-pose-report.json').write_text(json.dumps(dict(result='PASS_SHARED_OWNER_TIME_CAR_WORLD_SKY_DIAGNOSTIC',counts=dict(pose_counts),samples=pose_results,timing_windows=timing_windows,full_scene_60fps=False,live_enabled=False,hud_retained_history_and_visibility_not_synchronized=True,test_sha256=sha(Path(__file__))),indent=2))\nprint('OWNER_POSE_COUNTS',dict(pose_counts),flush=True)\n"+marker)
p=out/('owner-pose-real-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text)
r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=240);(out/'owner-pose-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
