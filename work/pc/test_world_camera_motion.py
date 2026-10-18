from pathlib import Path
import os,ctypes as C,json,hashlib,struct,math,argparse
import numpy as np
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-camera-motion-tests'
parser=argparse.ArgumentParser();parser.add_argument('--projected',action='store_true');options=parser.parse_args();library='world-camera-motion.dll'
if options.projected:out=base/'NFSUG-pc-world-mesh-motion-tests';library='world-mesh-motion.dll'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'motion-build-report.json').read_text());assert receipt['dll_sha256']==sha(out/library)
for name,digest in receipt['source_sha256'].items():assert sha(Path(name))==digest
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 dll=C.CDLL(str(out/library));core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
class Key(C.Structure):_fields_=[('epoch',Q),('refresh',U),('identity',U*5)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
sample=fn(dll,'nf_pc_world_camera_sample',[P,S,P,P,S,P,C.c_double,P,S]);points=fn(dll,'nf_pc_world_camera_points',[P,S,P,P,S,P,C.c_double,P,U,P]);road=fn(dll,'nf_pc_road_camera',[P,S,P,P]);world_open=fn(dll,'nf_pc_source_world',[P,U,S],P);world_close=fn(dll,'nf_pc_world_free',[P],None);world_info=fn(dll,'nf_pc_world_info',[P,P]);surface=fn(dll,'nf_pc_world_surface_buffer',[P,U,U,P,P]);surface_info=fn(dll,'nf_pc_world_surface_info',[P,U,P]);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
def blob(w,i,k):p=P();n=S();assert surface(w,i,k,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def wrap(v):return ((v+2**31)%2**32)-2**31
def short(v):return ((v+2**15)%2**16)-2**15
def reference(camera,p):
 m=struct.unpack_from('<12i',camera,8);x,z=math.floor(p[0]),math.floor(p[2]);fx,fz=p[0]-x,p[2]-z;r=[0.,p[1]+m[10],0.]
 for i in [0,1]:
  for j in [0,1]:
   weight=(fx if i else 1-fx)*(fz if j else 1-fz)
   for k in [0,2]:r[k]+=weight*short(wrap(wrap(wrap(x+i+m[9])*m[k])+wrap(wrap(z+j+m[11])*m[6+k]))>>14)
 return r
rigid=fn(dll,'nf_pc_world_rigid_points',[P,S,P,P,S,P,C.c_double,P,U,P]);model=fn(dll,'nf_pc_world_model',[P,U,P,P]);mesh=fn(dll,'nf_pc_world_mesh',[P,U,S],P);mesh_free=fn(dll,'nf_pc_world_mesh_free',[P],None);mesh_buffer=fn(dll,'nf_pc_world_mesh_buffer',[P,U,P,P])
last={};seen=set();tested=fractions=point_count=0;changed=0;missing={};kinds={};max_error=0.;kept=None;rigid_pairs=0
projected_pairs=projected_samples=projected_vertices=0;held_mesh=None;discrete_mode_pairs=0;last_projected=None
if options.projected:
 project=fn(dll,'nf_pc_world_motion_mesh',[P,S,U,P,P,S,U,P,C.c_double,S],P);mesh_info=fn(dll,'nf_pc_world_mesh_info',[P,P]);frame_component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P])
def mesh_bytes(m,kind):
 p=P();n=S();assert mesh_buffer(m,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def check_projected(a,ai,ak,b,bi,bk,raw,old_endpoint,new_endpoint,old_meta,new_meta):
 global projected_pairs,projected_samples,projected_vertices,held_mesh,discrete_mode_pairs,last_projected
 discrete_mode_pairs+=int(old_meta[4]!=new_meta[4])
 for alpha in [0.,1.,.25,.5,.75]:
  m=project(a,len(a),ai,C.byref(ak),b,len(b),bi,C.byref(bk),alpha,32*1024*1024)
  if not m:
   (out/'rejected-a.nsp').write_bytes(a);(out/'rejected-b.nsp').write_bytes(b);(out/'rejected-pair.json').write_text(json.dumps(dict(ai=ai,bi=bi,alpha=alpha,older=list(ak.identity),newer=list(bk.identity),old_metadata=old_meta,new_metadata=new_meta)))
  assert m,('Projected sampling rejected',ai,bi,alpha,old_meta,new_meta);info=(Q*16)();assert mesh_info(m,info)
  if alpha in [0.,1.]:
   expected,metadata=(old_endpoint,old_meta) if alpha==0 else (new_endpoint,new_meta)
   assert tuple(info)==metadata and [mesh_bytes(m,k) for k in [0,1]]==expected
  else:
   assert tuple(info[:12])==old_meta[:12]
   camera=np.frombuffer(mesh_bytes(m,1),dtype='<f8').reshape(-1,3);ring=[]
   for i,current in enumerate(camera):
    previous=camera[i-1];pa,pb=previous[2]>=64,current[2]>=64
    if pa!=pb:ring.append(previous+(current-previous)*((64-previous[2])/(current[2]-previous[2])))
    if pb:ring.append(current)
   vertices=np.frombuffer(mesh_bytes(m,0),dtype='<f4').reshape(-1,5);assert np.isfinite(vertices).all()
   # Independently check source camera clipping/projection, not ear order or UV.
   def projection(packet):
    section=struct.unpack_from('<I',packet,36)[0]
    if struct.unpack_from('<I',packet,section)[0]!=0x324d464e:section+=struct.unpack_from('<I',packet,section+8)[0]
    return np.array(struct.unpack_from('<3d',packet,section+24))
   cx,cy,scale=projection(a)*(1-alpha)+projection(b)*alpha
   if len(vertices):
    expected=np.array([[cx+scale*p[0]/p[2],cy+scale*p[1]/p[2],1. if info[13] else 1/p[2]] for p in ring]);assert len(expected)>=3
    for vertex in vertices:
     error=np.abs(expected-vertex[[0,1,4]])/(1+np.abs(expected));assert np.any(np.max(error,axis=1)<2e-6),(vertex,expected)
    triangles=vertices.reshape(-1,3,5);area=sum(abs((v[1,0]-v[0,0])*(v[2,1]-v[0,1])-(v[1,1]-v[0,1])*(v[2,0]-v[0,0])) for v in triangles)*.5;polygon=abs(sum(expected[i,0]*expected[(i+1)%len(expected),1]-expected[(i+1)%len(expected),0]*expected[i,1] for i in range(len(expected))))*.5;assert abs(area-polygon)<.01+polygon*2e-5
   projected_vertices+=len(vertices);projected_samples+=1
  if held_mesh is None:held_mesh=(m,mesh_bytes(m,0))
  else:mesh_free(m)
 projected_pairs+=1
 last_projected=(a,ai,Key.from_buffer_copy(ak),b,bi,Key.from_buffer_copy(bk))
def endpoint_camera(w,i):
 m=mesh(w,i,32*1024*1024);assert m;p=P();n=S();assert mesh_buffer(m,1,C.byref(p),C.byref(n));data=C.string_at(p,n.value);mesh_free(m);return data
def check_rigid(a,ak,b,bk,raw,old_endpoint,new_endpoint):
 global tested,fractions,point_count,max_error,rigid_pairs
 va=np.frombuffer(a,dtype='<f8');vb=np.frombuffer(b,dtype='<f8');qa=va[3:]/np.linalg.norm(va[3:]);qb=vb[3:]/np.linalg.norm(vb[3:]);d=float(qa@qb)
 if d<0:qb=-qb;d=-d
 d=min(1.,d);vertices=np.frombuffer(raw,dtype='<f8').reshape(-1,3);array=(C.c_double*(len(vertices)*3)).from_buffer_copy(raw)
 for alpha,endpoint in [(0.,old_endpoint),(1.,new_endpoint),(.25,None),(.5,None),(.75,None)]:
  output=(C.c_double*(len(vertices)*3))();assert rigid(a,56,C.byref(ak),b,56,C.byref(bk),alpha,array,len(vertices),output)
  if endpoint is not None:assert bytes(output)==endpoint
  else:
   if d>.9995:q=qa*(1-alpha)+qb*alpha
   else:angle=math.acos(d);q=(math.sin((1-alpha)*angle)*qa+math.sin(alpha*angle)*qb)/math.sin(angle)
   x,y,z,w=q/np.linalg.norm(q);rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]);expected=(vertices-(va[:3]*(1-alpha)+vb[:3]*alpha))@rotation.T;actual=np.array(output).reshape(-1,3);error=float(np.max(np.abs(actual-expected)));assert np.allclose(actual,expected,atol=1e-8,rtol=1e-10);max_error=max(max_error,error);fractions+=1
  point_count+=len(vertices)
 tested+=1;rigid_pairs+=1
def check(a,ak,b,bk,raw):
 global tested,fractions,point_count,max_error,kept
 vertices=list(struct.iter_unpack('<3d',raw));array=(C.c_double*(len(vertices)*3))(*[x for p in vertices for x in p])
 for alpha,endpoint in [(0.,a),(1.,b),(.25,None),(.5,None),(.75,None)]:
  camera=C.create_string_buffer(56);assert sample(a,56,C.byref(ak),b,56,C.byref(bk),alpha,camera,56)
  if endpoint:assert camera.raw==endpoint
  output=(C.c_double*(len(vertices)*3))();assert points(a,56,C.byref(ak),b,56,C.byref(bk),alpha,array,len(vertices),output)
  for i,p in enumerate(vertices):
   expected=reference(camera.raw,p);max_error=max(max_error,max(abs(output[i*3+k]-expected[k]) for k in range(3)));assert all(abs(output[i*3+k]-expected[k])<1e-9 for k in range(3))
   if endpoint:
    direct=(C.c_double*3)();assert road(endpoint,56,(C.c_double*3)(*p),direct);assert tuple(direct)==tuple(output[i*3:i*3+3])
  if endpoint is None:fractions+=1
  point_count+=len(vertices)
 tested+=1;kept=(a,ak,b,bk,raw)
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial)
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   frame=rcap(r,64*1024*1024)
   if not frame:continue
   try:
    fi=(Q*8)();assert frame_info(frame,fi)
    for owner in range(fi[4]):
     oi=(Q*5)();assert owner_info(frame,owner,oi);w=world_open(frame,owner,64*1024*1024);assert w;packet=None
     if options.projected:
      p=P();n=S();assert frame_component(frame,owner,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value)
     try:
      wi=(Q*4)();assert world_info(w,wi)
      for i in range(wi[0]):
       camera=blob(w,i,8);meta=(Q*12)();assert surface_info(w,i,meta)
       fixed=bool(camera)
       if not fixed:
        missing[str(meta[3])]=missing.get(str(meta[3]),0)+1;p=P();n=S();assert model(w,0,C.byref(p),C.byref(n)) and n.value>=104;camera=C.string_at(p.value+48,56)
       identity=struct.unpack('<5I',blob(w,i,9));key=Key(oi[0],oi[3],(U*5)(*identity));token=(key.epoch,identity);occurrence=(token,key.refresh)
       if occurrence in seen:continue
       seen.add(occurrence);raw=blob(w,i,0)
       if token in last:
        a,ak,previous,old_endpoint,old_fixed,old_packet,old_index,old_mesh=last[token]
        if 0<key.refresh-ak.refresh<=8:
         if previous==raw and old_fixed==fixed:
          if fixed:check(a,ak,camera,key,raw)
          else:check_rigid(a,ak,camera,key,raw,old_endpoint,endpoint_camera(w,i))
          if options.projected:
           current=mesh(w,i,32*1024*1024);assert current;mi=(Q*16)();assert mesh_info(current,mi);current_mesh=([mesh_bytes(current,k) for k in [0,1]],tuple(mi));mesh_free(current);check_projected(old_packet,old_index,ak,packet,i,key,raw,old_mesh[0],current_mesh[0],old_mesh[1],current_mesh[1])
          kinds[str(meta[3])]=kinds.get(str(meta[3]),0)+1
         else:changed+=1
       stored_mesh=None
       if options.projected:
        current=mesh(w,i,32*1024*1024);assert current;mi=(Q*16)();assert mesh_info(current,mi);stored_mesh=([mesh_bytes(current,k) for k in [0,1]],tuple(mi));mesh_free(current)
       last[token]=(camera,key,raw,None if fixed else endpoint_camera(w,i),fixed,packet,i,stored_mesh)
     finally:world_close(w)
   finally:frame_free(frame)
finally:rclose(r);close(h)
assert tested>20 and fractions==tested*3 and samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e',dict(tested=tested,fractions=fractions,changed=changed,missing=missing,seen=len(seen),keys=len(last),samples=samples,audio=digest.hexdigest());assert before=={str(p):sha(p) for p in [rom,state]}
sa=struct.pack('<2I12i',1,0x03000000,16384,0,0,0,16384,0,0,0,16384,0,0,0);sb=struct.pack('<2I12i',1,0x03000004,0,0,-16384,0,16384,0,16384,0,0,-10,4,-20);ka,kb=Key(1,1,(U*5)(1,2,3,4,5)),Key(1,2,(U*5)(1,2,3,4,5))
a,ak,b,bk=sa,ka,sb,kb;invalid=0
for alpha in [-1,2,float('nan')]:
 output=C.create_string_buffer(b'\xa5'*56);assert not sample(a,56,C.byref(ak),b,56,C.byref(bk),alpha,output,56) and output.raw==b'\xa5'*56+b'\0';invalid+=1
for field in ['epoch','refresh','identity']:
 bad=Key.from_buffer_copy(bk)
 if field=='epoch':bad.epoch+=1
 elif field=='refresh':bad.refresh=ak.refresh+9
 else:bad.identity[1]^=1
 output=C.create_string_buffer(b'\xa5'*56);assert not sample(a,56,C.byref(ak),b,56,C.byref(bad),.5,output,56) and output.raw==b'\xa5'*56+b'\0';invalid+=1
# Known 90-degree Y rotation: half phase must be a 45-degree view, with original
# signed translation convention and exact discrete source header.
sa=struct.pack('<2I12i',1,0x03000000,16384,0,0,0,16384,0,0,0,16384,0,0,0);sb=struct.pack('<2I12i',1,0x03000004,0,0,-16384,0,16384,0,16384,0,0,-10,4,-20);ka,kb=Key(1,1,(U*5)(1,2,3,4,5)),Key(1,2,(U*5)(1,2,3,4,5));output=C.create_string_buffer(56);assert sample(sa,56,C.byref(ka),sb,56,C.byref(kb),.5,output,56);assert struct.unpack('<2I12i',output.raw)==(1,0x03000000,11585,0,-11585,0,16384,0,11585,0,11585,-5,2,-10)
# Late invalid source point must not leave partially updated output.
bad_points=(C.c_double*6)(0,0,100,float('nan'),0,100);untouched=(C.c_double*6)(*([12345.]*6));assert not points(sa,56,C.byref(ka),sb,56,C.byref(kb),.5,bad_points,2,untouched) and list(untouched)==[12345.]*6;invalid+=1
rigid_invalid=0;pose_a=struct.pack('<7d',0,0,0,0,0,0,1);pose_b=struct.pack('<7d',10,0,20,0,0,0,1);good_points=(C.c_double*6)(0,0,100,10,0,100)
for alpha in [-1,2,float('nan')]:
 assert not rigid(pose_a,56,C.byref(ka),pose_b,56,C.byref(kb),alpha,good_points,2,untouched) and list(untouched)==[12345.]*6;rigid_invalid+=1
for field in ['epoch','refresh','identity']:
 bad=Key.from_buffer_copy(kb)
 if field=='epoch':bad.epoch+=1
 elif field=='refresh':bad.refresh=ka.refresh+9
 else:bad.identity[1]^=1
 assert not rigid(pose_a,56,C.byref(ka),pose_b,56,C.byref(bad),.5,good_points,2,untouched) and list(untouched)==[12345.]*6;rigid_invalid+=1
for bad_pose in [struct.pack('<7d',0,0,0,0,0,0,0),struct.pack('<7d',float('nan'),0,0,0,0,0,1)]:
 assert not rigid(bad_pose,56,C.byref(ka),pose_b,56,C.byref(kb),.5,good_points,2,untouched) and list(untouched)==[12345.]*6;rigid_invalid+=1
assert not rigid(pose_a,56,C.byref(ka),pose_b,56,C.byref(kb),.5,bad_points,2,untouched) and list(untouched)==[12345.]*6;rigid_invalid+=1
for count in [0,33]:
 assert not rigid(pose_a,56,C.byref(ka),pose_b,56,C.byref(kb),.5,good_points,count,untouched) and list(untouched)==[12345.]*6;rigid_invalid+=1
fixed_synthetic_points=0
for alpha in [0,.25,.5,.75,1]:
 sampled=C.create_string_buffer(56);assert sample(sa,56,C.byref(ka),sb,56,C.byref(kb),alpha,sampled,56)
 if alpha in [0,1]:assert sampled.raw==(sa if alpha==0 else sb)
 output=(C.c_double*6)();assert points(sa,56,C.byref(ka),sb,56,C.byref(kb),alpha,good_points,2,output)
 for i in range(2):assert tuple(output[i*3:i*3+3])==tuple(reference(sampled.raw,good_points[i*3:i*3+3]));fixed_synthetic_points+=1
report=dict(result='PASS_WORLD_SOURCE_CAMERA_COMPONENT',source_pairs=tested,fractional_samples=fractions,camera_points_compared=point_count,scalar_fixed_point_max_error=max_error,endpoint_camera_blobs_and_points_exact=True,known_rotation_translation_sample_verified=True,invalid_atomic_requests=invalid,source_kinds_with_camera_pairs=kinds,surface_occurrences_without_source_camera=missing,changed_static_points_not_sampled=changed,original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),rom_state_sha256=before,dll_sha256=sha(out/library),build_report_sha256=sha(out/'motion-build-report.json'),test_source_sha256=sha(Path(__file__)),live_integration=False,full_scene_60fps=False,quantized_camera=True,projection_visibility_retained_layers_not_implemented=True)
report.pop('scalar_fixed_point_max_error');report.pop('endpoint_camera_blobs_and_points_exact');report.pop('quantized_camera')
report['rigid_camera_source_pairs']=rigid_pairs;report['fixed_camera_source_pairs']=tested-rigid_pairs;report['fixed_camera_actual_replay_coverage']=tested>rigid_pairs;report['camera_points_max_error']=max_error;report['actual_rigid_endpoint_camera_points_byte_exact']=True;report['fixed_camera_synthetic_points']=fixed_synthetic_points;report['fixed_camera_synthetic_endpoint_blobs_exact']=True;report['rigid_invalid_atomic_requests']=rigid_invalid;report['optional_fixed_camera_quantized']=True;report['common_rigid_camera_quantized']=False;report['dll_sha256']=sha(out/library)
if options.projected:
 a,ai,ak,b,bi,bk=last_projected;bad=Key.from_buffer_copy(bk);bad.identity[2]^=1;negative=0
 for alpha in [-1,2,float('nan')]:assert not project(a,len(a),ai,C.byref(ak),b,len(b),bi,C.byref(bk),alpha,32*1024*1024);negative+=1
 assert not project(a,len(a),ai,C.byref(ak),b,len(b),bi,C.byref(bad),.5,32*1024*1024);negative+=1
 assert not project(a,91,ai,C.byref(ak),b,len(b),bi,C.byref(bk),.5,32*1024*1024);negative+=1
 assert not project(a,len(a),999,C.byref(ak),b,len(b),bi,C.byref(bk),.5,32*1024*1024);negative+=1
 assert not project(a,len(a),ai,C.byref(ak),b,len(b),bi,C.byref(bk),.5,1);negative+=1
 changed_packet=bytearray(b);at=struct.unpack_from('<I',b,48)[0]+8
 for _ in range(bi):
  count,width,height=struct.unpack_from('<3I',b,at);at+=12+count*40+width*height*4
 struct.pack_into('<d',changed_packet,at+12,struct.unpack_from('<d',b,at+12)[0]+1);changed_packet=bytes(changed_packet);assert not project(a,len(a),ai,C.byref(ak),changed_packet,len(changed_packet),bi,C.byref(bk),.5,32*1024*1024);negative+=1
 assert projected_pairs==tested and projected_samples==tested*3 and held_mesh;assert mesh_bytes(held_mesh[0],0)==held_mesh[1];mesh_free(held_mesh[0]);report.update(result='PASS_WORLD_PROJECTED_MOTION_COMPONENT',projected_pairs=projected_pairs,projected_fractional_samples=projected_samples,projected_triangle_vertices=projected_vertices,endpoint_mesh_metadata_buffers_exact=True,independent_projected_points_and_area_verified=True,mesh_outlives_source_and_core=True,projection_visibility_retained_layers_not_implemented=False,visibility_retained_layers_not_implemented=True,discrete_render_mode_transition_pairs=discrete_mode_pairs)
 report['projected_invalid_requests_rejected']=negative
(out/'motion-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
