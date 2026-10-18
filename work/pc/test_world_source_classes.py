from pathlib import Path
import hashlib,subprocess,os
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-world-source-class-tests'
paths=list((base/'NFSUG-pc-scene-region-tests').glob('real-region-*.py'));assert len(paths)==1
text=paths[0].read_text().replace("out=base/'NFSUG-pc-scene-region-tests'","out=base/'NFSUG-pc-world-source-class-tests'").replace('scene-regions.dll','world-source-classes.dll').replace("'nf_pc_scene_prepare'","'nf_pc_scene_prepare_motion'")
extra=r'''
batch_prepare=fn(d,'nf_pc_scene_world_pose_owner',[P,U,P,U,C.c_double,S],P);batch_free=fn(d,'nf_pc_world_motion_owner_free',[P],None);batch_info=fn(d,'nf_pc_world_motion_owner_info',[P,P]);class_mesh=fn(d,'nf_pc_world_motion_owner_class_mesh',[P,U,S],P);class_material=fn(d,'nf_pc_world_motion_owner_class_material',[P,U,P,P]);mesh_free=fn(d,'nf_pc_world_mesh_free',[P],None);mesh_buffer=fn(d,'nf_pc_world_mesh_buffer',[P,U,P,P]);reference=fn(d,'nf_pc_world_motion_mesh',[P,S,U,P,P,S,U,P,C.c_double,S],P);packet_view=fn(d,'nf_pc_scene_motion_packet',[P,U,P,P]);world_surface=fn(d,'nf_pc_world_surface_buffer',[P,U,U,P,P]);strict_world_pose=fn(d,'nf_pc_scene_world_pose',[P,U,P,U,C.c_double,S],P);scene_vertices=fn(d,'nf_pc_scene_command_buffer',[P,U,U,P,P])
raw_prepare=fn(d,'nf_pc_world_motion_owner_prepare',[P,S,P,P,S,P,C.c_double,S],P)
class MotionKey(C.Structure):_fields_=[('epoch',Q),('refresh',U),('identity',U*5)]
class_counts=Counter();kept_mesh=None;class_seen=set()
def blob(f,*args):
 p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def exercise_classes(old,new,ai,aa,ao,bi,bb,bo):
 global kept_mesh
 pair=rp(old,new,256*1024);assert pair;pi=(Q*16)();assert ri(pair,pi)
 try:
  for band in range(pi[6]):
   v=(Q*9)();assert rb(pair,band,v);top,bottom,ar,br,first,count,mode,oldcount,newcount=v
   if mode!=2:continue
   batch=batch_prepare(old,ar,new,br,.5,64*1024*1024)
   if not batch:class_counts['unsupported_owner_batches']+=1;continue
   zero=batch_prepare(old,ar,new,br,0,64*1024*1024);assert zero;class_counts['forward_owner_batches']+=1
   try:
    wi=(Q*14)();assert batch_info(batch,wi) and wi[6]==3;class_counts['source_owner_decode_count']+=wi[6]
    oldpacket=blob(packet_view,old,ar);newpacket=blob(packet_view,new,br)
    for j in range(first,first+count):
     row=(Q*8)();ids=(U*5)();assert rr(pair,j,row,ids);status,oi,ni,bandindex,flags,oldorder,neworder,kind=row
     if status!=4 or oi==0xffffffff or kind==3:continue
     token=(bi[1],ar,br,oi)
     if token in class_seen:continue
     class_seen.add(token);a=aa[oi];surface=a[0][2];targets=[(k,c) for k,c in enumerate(bb) if c[0][0]==br and c[2]==a[2]];assert targets
     assert not strict_world_pose(old,oi,new,targets[0][0],.5,32*1024*1024)
     m=class_mesh(batch,surface,32*1024*1024)
     if not m:class_counts['unsupported_class_surface']+=1;continue
     try:
      vertices=blob(mesh_buffer,m,0);z=class_mesh(zero,surface,32*1024*1024);assert z
      try:assert blob(mesh_buffer,z,0)==blob(scene_vertices,old,oi,0)
      finally:mesh_free(z)
      if not class_counts['guard_scenario_checked']:
       ak_owner=(Q*5)(*a[1]);bk_owner=(Q*5)(*targets[0][1][1])
       end=raw_prepare(oldpacket,len(oldpacket),ak_owner,newpacket,len(newpacket),bk_owner,1,64*1024*1024);assert end
       try:
        assert not class_mesh(end,surface,32*1024*1024)
        p=P(0x1234);idx=U(0x5678);assert not class_material(end,surface,C.byref(p),C.byref(idx)) and p.value==0x1234 and idx.value==0x5678
       finally:batch_free(end)
       assert not batch_prepare(old,ar,new,br,.5,wi[5]-1);exact=batch_prepare(old,ar,new,br,.5,wi[5]);assert exact
       try:
        exactmesh=class_mesh(exact,surface,32*1024*1024);assert exactmesh
        try:assert blob(mesh_buffer,exactmesh,0)==vertices
        finally:mesh_free(exactmesh)
       finally:batch_free(exact)
       changed=bytearray(newpacket);at=struct.unpack_from('<I',changed,48)[0]+8
       for k in range(targets[0][1][0][2]):
        corners,w,h=struct.unpack_from('<3I',changed,at);at+=12+corners*40+w*h*4
       x=struct.unpack_from('<d',changed,at+12)[0];struct.pack_into('<d',changed,at+12,x+1)
       changed=bytes(changed);incompatible=raw_prepare(oldpacket,len(oldpacket),ak_owner,changed,len(changed),bk_owner,.5,64*1024*1024);assert incompatible
       try:assert not class_mesh(incompatible,surface,32*1024*1024)
       finally:batch_free(incompatible)
       class_counts['guard_scenario_checked']+=1
      if vertices!=blob(scene_vertices,old,oi,0):class_counts['moving_ambiguous_surfaces']+=1
      # Check EVERY newer alias gives the same source-camera mesh. No target is
      # chosen by the class sampler itself; older command indices stay intact.
      for target,c in targets:
       ak=MotionKey(a[1][0],a[1][3],(U*5)(*a[2]));bk=MotionKey(c[1][0],c[1][3],(U*5)(*c[2]));r=reference(oldpacket,len(oldpacket),surface,C.byref(ak),newpacket,len(newpacket),c[0][2],C.byref(bk),.5,32*1024*1024);assert r
       try:assert blob(mesh_buffer,r,0)==vertices;class_counts['all_new_alias_reference_checks']+=1
       finally:mesh_free(r)
      material_world=P();material_surface=U(0xffffffff);assert class_material(batch,surface,C.byref(material_world),C.byref(material_surface)) and material_surface.value==surface
      original=world_decode(oldpacket,len(oldpacket),64*1024*1024);assert original
      try:
       for field in [2,3,4]:assert blob(world_surface,material_world,surface,field)==blob(world_surface,original,surface,field)
      finally:world_free(original)
      class_counts['preserved_older_duplicate_commands']+=1;class_counts['source_kind_'+str(kind)]+=1
      if kept_mesh:mesh_free(kept_mesh[0])
      kept_mesh=(m,vertices);m=None
     finally:
      if m:mesh_free(m)
    assert not class_mesh(batch,0xffffffff,32*1024*1024) and not class_mesh(batch,0,0)
    p=P(0x1234);index=U(0x5678);assert not class_material(batch,0xffffffff,C.byref(p),C.byref(index)) and p.value==0x1234 and index.value==0x5678
    assert not batch_prepare(old,ar,new,br,1,64*1024*1024) and not batch_prepare(old,ar,new,br,float('nan'),64*1024*1024) and not batch_prepare(None,ar,new,br,.5,64*1024*1024)
   finally:batch_free(batch);batch_free(zero)
 finally:rf(pair)
'''
marker='region_counts=Counter();held_region=None;held_region_snapshot=None';assert text.count(marker)==1;text=text.replace(marker,marker+'\n'+extra)
marker='ai,aa,ao=scene(old);bi,bb,bo=scene(new);pair=rp(old,new,256*1024);assert pair;';assert text.count(marker)==1;text=text.replace(marker,'ai,aa,ao=scene(old);bi,bb,bo=scene(new);exercise_classes(old,new,ai,aa,ao,bi,bb,bo);pair=rp(old,new,256*1024);assert pair;')
marker="print('REGION_COUNTS',dict(region_counts),flush=True)";assert text.count(marker)==1
addition=r'''
assert kept_mesh and class_counts['preserved_older_duplicate_commands']>0 and class_counts['moving_ambiguous_surfaces']>0
assert blob(mesh_buffer,kept_mesh[0],0)==kept_mesh[1];mesh_free(kept_mesh[0])
(out/'class-test-report.json').write_text(json.dumps(dict(result='PASS_WORLD_SOURCE_CLASS_CAMERA_SAMPLING_WITHOUT_CORRESPONDENCE',counts=dict(class_counts),all_new_aliases_same_sampled_geometry=True,older_duplicate_commands_and_materials_preserved=True,exact_alpha0_endpoint_vertices=True,scene_core_and_owner_destruction_survived=True,original_frames_and_pcm_exact=True,build_exe_sha256=b['exe_sha256'],dll_sha256=b['identity_dll_sha256'],core_sha256=b['core_sha256'],test_sha256=sha(Path(__file__)),full_scene_60fps=False,live_motion_enabled=False),indent=2))
print('CLASS_COUNTS',dict(class_counts),flush=True)
'''
text=text.replace(marker,marker+'\n'+addition)
p=out/('class-real-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text)
r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=150);(out/'class-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
