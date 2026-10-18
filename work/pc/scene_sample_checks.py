sample_range=fn(d,'nf_pc_scene_sample_range',[P,P,P,P,P]);sample_prepare=fn(d,'nf_pc_scene_sample_prepare',[P,P,C.c_double,U,S,P],P);sample_free=fn(d,'nf_pc_scene_sample_free',[P],None);sample_info=fn(d,'nf_pc_scene_sample_info',[P,P,P]);sample_band=fn(d,'nf_pc_scene_sample_band',[P,U,P,P]);sample_command=fn(d,'nf_pc_scene_sample_command',[P,U,P]);sample_draw=fn(d,'nf_pc_scene_gpu_draw_sample',[P,P,U,U,U,U,U,P,S]);sample_counts=Counter()
def sample_check(old,new,aa,bb,pair,pi):
 bands=[];lo=0;hi=float('inf');forward=0;broken=False
 for k in range(pi[6]):
  v=(Q*9)();assert rb(pair,k,v);bands.append(tuple(v));broken|=v[6]==3
  if v[6]!=2:continue
  forward+=1;at=struct.unpack_from('<16Q',blob(scene_time,old,v[2]));bt=struct.unpack_from('<16Q',blob(scene_time,new,v[3]));sa=struct.unpack_from('<I',blob(sky_view,old,v[2]),16)[0];sb=struct.unpack_from('<I',blob(sky_view,new,v[3]),16)[0];lo=max(lo,at[6],sa);hi=min(hi,bt[6],sb)
 x=C.c_double(-7);y=C.c_double(-9);reason=U(99);valid=sample_range(old,new,C.byref(x),C.byref(y),C.byref(reason));sample_counts['pairs']+=1
 assert bool(valid)==bool(forward and not broken and lo<hi)
 if not valid:
  assert x.value==-7 and y.value==-9;sample_counts['range_reject_'+str(reason.value)]+=1
 else:assert x.value==lo and y.value==hi
 # Complete endpoints must remain exact even when an interior target is unavailable.
 if sample_counts['endpoint_pairs']<3:
  for mode,base_scene in [(0,old),(1,new)]:
   p=sample_prepare(old,new,0,mode,64*1024*1024,C.byref(reason));assert p,reason.value
   try:
    for w,h,aw,ah in [(3840,2160,3240,2160),(613,407,601,399)]:
     n=w*h*4;a=C.create_string_buffer(n);z=C.create_string_buffer(n);assert gpu_draw(gpu,base_scene,w,h,aw,ah,15,a,n) and sample_draw(gpu,p,w,h,aw,ah,15,z,n),gpu_error();assert a.raw==z.raw;sample_counts['endpoint_exact_pixels']+=w*h
   finally:sample_free(p)
  sample_counts['endpoint_pairs']+=1
 if not valid:return
 target=(lo+hi)/2;p=sample_prepare(old,new,target,2,64*1024*1024,C.byref(reason));assert p,('prepare',reason.value,lo,hi,bands)
 try:
  info=(Q*16)();time=C.c_double();assert sample_info(p,info,C.byref(time)) and time.value==target and info[2]==pi[6] and info[15]==31
  cursor=0;new_only=0
  for k,v in enumerate(bands):
   stats=(Q*12)();fractions=(C.c_double*2)();assert sample_band(p,k,stats,fractions);assert tuple(stats[:5])==(v[0],v[1],v[2],v[3],v[6]) and stats[5]==cursor
   expected=[j for j,c in enumerate(aa) if c[0][0]==v[2]];mapping={}
   for j in range(v[4],v[4]+v[5]):
    row=(Q*8)();ids=(U*5)();assert rr(pair,j,row,ids)
    if row[1]==0xffffffff:new_only+=1
    else:mapping[row[1]]=tuple(row)
   assert stats[6]==len(expected)
   for j in expected:
    trace=(Q*5)();assert sample_command(p,cursor,trace);assert tuple(trace[:3])==(j,k,mapping[j][0]);assert bool(trace[4]&2)==(mapping[j][0]==2);cursor+=1
   if v[6]==2:
    at=struct.unpack_from('<16Q',blob(scene_time,old,v[2]));bt=struct.unpack_from('<16Q',blob(scene_time,new,v[3]));assert abs(fractions[0]-(target-at[6])/(bt[6]-at[6]))<1e-12
   else:assert fractions[0]==0
  assert info[3]==cursor and info[10]==new_only and info[3]==info[4]+info[5]+info[7];sample_counts['interior_plans']+=1;sample_counts['model_samples']+=info[4];sample_counts['world_samples']+=info[5];sample_counts['held_draws']+=info[7];sample_counts['unsupported_draws']+=info[8]
  if sample_counts['budget_pairs']<2:
   exact=sample_prepare(old,new,target,2,info[12],C.byref(reason));assert exact,reason.value;sample_free(exact);assert not sample_prepare(old,new,target,2,info[12]-1,C.byref(reason)) and reason.value==4;sample_counts['budget_pairs']+=1
  for bad in [float('nan'),lo-1,hi]:assert not sample_prepare(old,new,bad,2,64*1024*1024,C.byref(reason));sample_counts['time_guards']+=1
  sentinel=(Q*5)(*[123]*5);assert not sample_command(p,info[3],sentinel) and list(sentinel)==[123]*5;sample_counts['getter_guards']+=1
  if sample_counts['interior_gpu_cases']<3 and info[4]+info[5]:
   n=3840*2160*4;a=C.create_string_buffer(n);z=C.create_string_buffer(n);assert gpu_draw(gpu,old,3840,2160,3240,2160,15,a,n) and sample_draw(gpu,p,3840,2160,3240,2160,15,z,n),gpu_error();sample_counts['interior_gpu_cases']+=1;sample_counts['visibly_changed_cases']+=a.raw!=z.raw
   # Parent caches/geometry must survive the sampled submission unchanged.
   again=C.create_string_buffer(n);assert gpu_draw(gpu,old,3840,2160,3240,2160,15,again,n) and a.raw==again.raw
   pixels=np.frombuffer(z.raw,dtype=np.uint8).reshape(2160,3840,4);assert not pixels[:,3240:].any();sample_counts['outside_active_pixels_zero']+=600*2160
 finally:sample_free(p)
 (out/'scene-sample-test-report.json').write_text(json.dumps(dict(result='PASS_PROGRESS',counts=dict(sample_counts),full_scene_60fps=False,live_interpolation=False),indent=2))
