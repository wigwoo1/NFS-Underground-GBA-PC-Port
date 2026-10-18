import time as bench_time
reference_counts=Counter();reference_patterns=set();plan_times=[];reference_cases=[]
retention_cases=[]
sample_submit=fn(d,'nf_pc_scene_gpu_render_sample',[P,P,U,U,U,U])
untimed_capture=fn(d,'nf_pc_source_frame_capture',[P,S],P)
retention_view=fn(d,'nf_pc_scene_retention_buffer',[P,U,U,U,P,P])

def reference_image(old,new,aa,pair,bands,target,w,h,aw,ah,passes):
 # Build EACH full original-owner reference using independently requested meshes.
 # Only then crop pixel-center band rows in readback coordinates. This never
 # reads a sample-plan command, mesh, background, or private struct.
 n=w*h*4;combined=np.zeros((h,w,4),dtype=np.uint8)
 for band,v in enumerate(bands):
  count=len(aa);worlds=(P*count)();models=(P*count)();owned_w=[];owned_m=[];batch=None;sky=None;bg=None
  try:
   if v[6]==2:
    at=struct.unpack_from('<16Q',blob(scene_time,old,v[2]));bt=struct.unpack_from('<16Q',blob(scene_time,new,v[3]));alpha=(target-at[6])/(bt[6]-at[6]);assert 0<=alpha<1
    packet_a=blob(sky_view,old,v[2]);packet_b=blob(sky_view,new,v[3]);ka=(Q*5)();kb=(Q*5)();assert ro(pair,band,0,ka) and ro(pair,band,1,kb)
    sky=sky_decode(packet_a,len(packet_a),ka,packet_b,len(packet_b),kb,65536);assert sky
    sky_times=(Q*7)();assert sky_info(sky,sky_times);bg,_=background_at(old,v[2],sky,(target-sky_times[1])/(sky_times[2]-sky_times[1]))
    if alpha>0:
     batch=batch_prepare(old,v[2],new,v[3],alpha,64*1024*1024)
     mapping={}
     for j in range(v[4],v[4]+v[5]):
      row=(Q*8)();ids=(U*5)();assert rr(pair,j,row,ids)
      if row[1]!=0xffffffff:mapping[row[1]]=tuple(row)
     for j,c in enumerate(aa):
      if c[0][0]!=v[2]:continue
      if c[0][1]:
       row=mapping[j]
       if row[0]==1:
        mesh=model_pose(old,j,new,row[2],alpha,32*1024*1024)
        if mesh:models[j]=mesh;owned_m.append(mesh)
      elif batch:
       mesh=class_mesh(batch,c[0][2],32*1024*1024)
       if mesh:worlds[j]=mesh;owned_w.append(mesh)
   image=C.create_string_buffer(n)
   assert pose_draw(gpu,old,worlds,models,count,bg,len(bg) if bg else 0,w,h,aw,ah,passes,image,n),gpu_error()
   top=math.ceil(v[0]*ah/160-.5);bottom=math.ceil(v[1]*ah/160-.5);source=np.frombuffer(image.raw,dtype=np.uint8).reshape(h,w,4);combined[ah-bottom:ah-top]=source[ah-bottom:ah-top]
  finally:
   for mesh in owned_w:mesh_free(mesh)
   for mesh in owned_m:model_free(mesh)
   if batch:batch_free(batch)
   if sky:sky_free(sky)
 return combined.tobytes()

def independent_band_check(old,new,aa,pair,bands,target,p,info):
 key=tuple(v[6] for v in bands)
 if key not in reference_patterns and len(reference_patterns)<8:
  reference_patterns.add(key)
  for w,h,aw,ah in [(3840,2160,3240,2160),(613,407,601,399)]:
   for passes in [1,4,7,15]:
    expected=reference_image(old,new,aa,pair,bands,target,w,h,aw,ah,passes);actual=C.create_string_buffer(w*h*4);assert sample_draw(gpu,p,w,h,aw,ah,passes,actual,len(actual)),gpu_error()
    if expected!=actual.raw:
     x=np.frombuffer(expected,dtype=np.uint8);y=np.frombuffer(actual.raw,dtype=np.uint8);changed=np.flatnonzero(x!=y);raise AssertionError(('band reference mismatch',key,w,h,passes,len(changed),int(changed[0])))
    reference_counts['exact_reference_pixels']+=w*h;reference_counts['reference_renders']+=1
   if w==3840:
    without=C.create_string_buffer(w*h*4);assert sample_draw(gpu,p,w,h,aw,ah,13,without,len(without)),gpu_error()
    full=np.frombuffer(actual.raw,dtype=np.uint8).reshape(h,w,4);no_retention=np.frombuffer(without.raw,dtype=np.uint8).reshape(h,w,4)
    visible=int(np.count_nonzero(np.any(full!=no_retention,axis=2)));record_counts=Counter()
    for v in bands:
     for kind in [2,3]:
      raw=blob(retention_view,old,v[2],kind,1);assert len(raw)%16==0
      for cell,asset,offset,refresh in struct.iter_unpack('<4I',raw):
       if not v[0]<=cell//240<v[1]:continue
       record_counts['retained_cells']+=1;record_counts['source_refresh_before_target' if refresh<target else 'source_refresh_after_target' if refresh>target else 'source_refresh_at_target']+=1
    retention_cases.append(dict(modes=list(key),target=target,visible_retention_pixels_after_hud=visible,source_record_counts=dict(record_counts)))
    reference_counts['retention_visibility_cases']+=1;reference_counts['visible_retention_pixels_after_hud']+=visible
  assert sample_submit(gpu,p,3840,2160,3240,2160),gpu_error();reference_counts['no_readback_submissions']+=1
  reference_cases.append(dict(modes=list(key),bands=[list(v[:4]) for v in bands],target=target,models=int(info[4]),worlds=int(info[5]),held=int(info[7])))
 if not reference_counts['missing_timing_pairs']:
  frame2=untimed_capture(C.byref(api),64*1024*1024);assert frame2
  try:untimed=prepare(frame2,64*1024*1024);assert untimed
  finally:frame_free(frame2)
  try:
   x=C.c_double(-3);y=C.c_double(-5);reason=U();assert not sample_range(old,untimed,C.byref(x),C.byref(y),C.byref(reason)) and reason.value==5 and x.value==-3 and y.value==-5
   assert not sample_prepare(old,untimed,target,2,64*1024*1024,C.byref(reason)) and reason.value==5
   # Optional timing failure must still allow the complete native endpoint.
   endpoint=sample_prepare(old,untimed,target,1,64*1024*1024,C.byref(reason));assert endpoint
   try:
    n=613*407*4;a=C.create_string_buffer(n);b=C.create_string_buffer(n);assert gpu_draw(gpu,untimed,613,407,601,399,15,a,n) and sample_draw(gpu,endpoint,613,407,601,399,15,b,n) and a.raw==b.raw
   finally:sample_free(endpoint)
   reference_counts['missing_timing_pairs']+=1;reference_counts['native_endpoint_survives_optional_failure']+=1
  finally:scene_free(untimed)
 x=C.c_double(-3);y=C.c_double(-5);reason=U();assert not sample_range(new,old,C.byref(x),C.byref(y),C.byref(reason)) and reason.value==2 and x.value==-3 and y.value==-5;reference_counts['reverse_pair_guards']+=1

def reset_composition_guards(h,old):
 assert load(h,data,len(data))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 newer=None
 for index in range(32):
  assert step(h,1);frame2=capture(C.byref(api),64*1024*1024,C.cast(timing_read,P))
  if not frame2:continue
  try:newer=prepare(frame2,64*1024*1024)
  finally:frame_free(frame2)
  if newer:break
 assert newer
 try:
  ai=(Q*8)();bi=(Q*8)();assert sinfo(old,ai) and sinfo(newer,bi) and ai[0]!=bi[0]
  x=C.c_double(-3);y=C.c_double(-5);reason=U();assert not sample_range(old,newer,C.byref(x),C.byref(y),C.byref(reason)) and reason.value==2 and x.value==-3 and y.value==-5
  for mode in [0,1,2]:assert not sample_prepare(old,newer,0,mode,64*1024*1024,C.byref(reason)) and reason.value==2
  reference_counts['natural_reset_epoch_guards']+=4
  # Ordinary endpoint remains a valid native draw after reset, without pairing epochs.
  image=C.create_string_buffer(613*407*4);assert gpu_draw(gpu,newer,613,407,601,399,15,image,len(image));reference_counts['reset_native_endpoint_draws']+=1
 finally:scene_free(newer)
