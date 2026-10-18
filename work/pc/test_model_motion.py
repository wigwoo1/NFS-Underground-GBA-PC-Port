from pathlib import Path
import os,ctypes as C,json,hashlib,struct,math
import numpy as np
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-model-motion-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'motion-build-report.json').read_text());assert receipt['dll_sha256']==sha(out/'model-motion.dll')
for name,digest in receipt['source_sha256'].items():assert sha(Path(name))==digest
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 dll=C.CDLL(str(out/'model-motion.dll'));core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
class Key(C.Structure):_fields_=[('epoch',Q),('refresh',U),('identity',U*5)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
sample=fn(dll,'nf_pc_model_motion_sample',[P,S,P,P,S,P,C.c_double,S],P);decode=fn(dll,'nf_pc_model_mesh_decode',[P,S,S],P);free=fn(dll,'nf_pc_model_mesh_free',[P],None);buffer=fn(dll,'nf_pc_model_mesh_buffer',[P,U,P,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
def blob(mesh,kind):p=P();n=S();assert buffer(mesh,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def u32(data,at=0):return struct.unpack_from('<I',data,at)[0]
def rotation(q):
 q=np.array(q,dtype=float);q/=np.linalg.norm(q);x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def interpolate(a,b,t):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);qa=a[3:]/np.linalg.norm(a[3:]);qb=b[3:]/np.linalg.norm(b[3:]);dot=np.dot(qa,qb)
 if dot<0:qb=-qb;dot=-dot
 dot=min(1.,dot)
 if dot>.9995:q=qa*(1-t)+qb*t
 else:angle=math.acos(dot);q=(math.sin((1-t)*angle)*qa+math.sin(t*angle)*qb)/math.sin(angle)
 return (a[:3]*(1-t)+b[:3]*t,q/np.linalg.norm(q))
maximum=32*1024*1024;tested=0;fractions=0;max_error=0.;rejected_geometry=0;seen=set();last={};guard_checks=0;kept=None;changed_regions={name:0 for name in ['layout','local_vertices','face_indices','UV','material']};material_transition_pairs=0
def check(a,ak,b,bk):
 global tested,fractions,max_error,kept
 for t,data in [(0.,a),(1.,b)]:
  m=sample(a,len(a),C.byref(ak),b,len(b),C.byref(bk),t,maximum);endpoint=decode(data,len(data),maximum);assert m and endpoint
  for kind in range(4):assert blob(m,kind)==blob(endpoint,kind)
  free(m);free(endpoint)
 anchor=decode(a,len(a),maximum);assert anchor;materials=[blob(anchor,kind) for kind in [2,3]];free(anchor)
 for t in [.25,.5,.75]:
  m=sample(a,len(a),C.byref(ak),b,len(b),C.byref(bk),t,maximum);assert m
  cam=interpolate(struct.unpack_from('<7d',a,48),struct.unpack_from('<7d',b,48),t);obj=interpolate(struct.unpack_from('<7d',a,104),struct.unpack_from('<7d',b,104),t);vertices=np.frombuffer(a,dtype='<f8',count=u32(a,4)*3,offset=160).reshape(-1,3)
  expected=((vertices@rotation(obj[1]).T+obj[0]-cam[0])@rotation(cam[1]).T);actual=np.frombuffer(blob(m,1),dtype='<f8').reshape(-1,3);error=float(np.max(np.abs(actual-expected)));assert np.allclose(actual,expected,rtol=1e-10,atol=1e-8);assert [blob(m,kind) for kind in [2,3]]==materials;max_error=max(max_error,error);free(m);fractions+=1
 tested+=1;kept=(a,ak,b,bk)
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
    info=(Q*8)();assert frame_info(frame,info)
    for owner in range(info[4]):
     owned=(Q*5)();assert owner_info(frame,owner,owned);p=P();n=S();assert component(frame,owner,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value);sections=[packet[u32(packet,36+i*12):u32(packet,36+i*12)+u32(packet,40+i*12)] for i in range(5)];model,world,_,_,ids=sections;count=1 if u32(model)==0x324d464e else u32(model,4);surfaces=u32(world,4)
     for mi in range(count):
      raw=model if count==1 else model[u32(model,8+mi*8):u32(model,8+mi*8)+u32(model,12+mi*8)];identity=struct.unpack_from('<5I',ids,8+(surfaces+mi)*20);key=Key(owned[0],owned[3],(U*5)(*identity));token=(key.epoch,tuple(identity));occurrence=(token,key.refresh)
      if occurrence in seen:continue
      seen.add(occurrence)
      if token in last:
       a,ak=last[token]
       if 0<key.refresh-ak.refresh<=8:
        geometry_end=160+u32(a,4)*24+u32(a,8)+u32(a,12)*18
        if len(a)==len(raw) and a[:24]==raw[:24] and a[160:geometry_end]==raw[160:geometry_end]:
         material_transition_pairs+=int(a[geometry_end:]!=raw[geometry_end:]);check(a,ak,raw,key)
        else:
         assert not sample(a,len(a),C.byref(ak),raw,len(raw),C.byref(key),.5,maximum);rejected_geometry+=1
         if len(a)!=len(raw) or a[:24]!=raw[:24]:changed_regions['layout']+=1
         else:
          v=160+u32(a,4)*24;f=v+u32(a,8)+u32(a,12)*2;uv=f+u32(a,12)*16
          for name,lo,hi in [('local_vertices',160,v),('face_indices',v,f),('UV',f,uv),('material',uv,len(a))]:changed_regions[name]+=int(a[lo:hi]!=raw[lo:hi])
      last[token]=(raw,key)
   finally:frame_free(frame)
finally:rclose(r);close(h)
assert tested>20 and fractions==tested*3 and samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';assert before=={str(p):sha(p) for p in [rom,state]}
a,ak,b,bk=kept
for alpha in [-.1,1.1,float('nan'),float('inf')]:assert not sample(a,len(a),C.byref(ak),b,len(b),C.byref(bk),alpha,maximum);guard_checks+=1
for field in ['epoch','refresh','identity']:
 bad=Key.from_buffer_copy(bk)
 if field=='epoch':bad.epoch+=1
 elif field=='refresh':bad.refresh=ak.refresh
 else:bad.identity[2]^=1
 assert not sample(a,len(a),C.byref(ak),b,len(b),C.byref(bad),.5,maximum);guard_checks+=1
assert not sample(a,len(a),C.byref(ak),b,len(b),C.byref(bk),.5,1);guard_checks+=1
for offset,value in [(0,b'BAD!'),(48,struct.pack('<7d',0,0,0,0,0,0,0)),(160,struct.pack('<d',float('nan')))]:
 bad=bytearray(a);bad[offset:offset+len(value)]=value;bad=bytes(bad);assert not sample(bad,len(bad),C.byref(ak),bad,len(bad),C.byref(bk),.5,maximum);guard_checks+=1
assert not sample(a,159,C.byref(ak),b,159,C.byref(bk),.5,maximum);guard_checks+=1
bad_key=Key.from_buffer_copy(bk);bad_key.refresh=ak.refresh+9;assert not sample(a,len(a),C.byref(ak),b,len(b),C.byref(bad_key),.5,maximum);guard_checks+=1
changed=bytearray(b);struct.pack_into('<d',changed,160,struct.unpack_from('<d',b,160)[0]+1);changed=bytes(changed);assert not sample(a,len(a),C.byref(ak),changed,len(changed),C.byref(bk),.5,maximum);guard_checks+=1
# A sampled result remains independently owned after source buffers and core die.
m=sample(a,len(a),C.byref(ak),b,len(b),C.byref(bk),.5,maximum);assert m;owned=blob(m,1);del a,b,last;assert blob(m,1)==owned;free(m)
def triangle(z):
 return struct.pack('<6I3d14d',0x324d464e,3,1,3,1,1,120,80,10,0,0,0,0,0,0,1,0,0,z,0,0,0,1)+struct.pack('<9d',-1,-1,0,-1,1,0,1,-1,0)+bytes([3])+struct.pack('<3H',0,1,2)+struct.pack('<6d',0,0,0,1,1,0)+b'\xff'*4
near_a,near_b=triangle(.75),triangle(1.25);near_ak,near_bk=Key(1,1,(U*5)(3,1,2,3,0)),Key(1,2,(U*5)(3,1,2,3,0));mesh_info=fn(dll,'nf_pc_model_mesh_info',[P,P]);near_counts=[]
for alpha in [0,.25,.5,.75,1]:
 m=sample(near_a,len(near_a),C.byref(near_ak),near_b,len(near_b),C.byref(near_bk),alpha,maximum);assert m;info=(Q*12)();assert mesh_info(m,info);near_counts.append(info[4]);free(m)
assert near_counts==[0,0,3,3,3],near_counts
report=dict(result='PASS_SOURCE_MODEL_POSE_SAMPLING_COMPONENT',original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),tested_source_pairs=tested,fractional_samples=fractions,endpoint_buffers_byte_exact=True,independent_numpy_camera_vertex_max_error=max_error,source_geometry_changes_rejected=rejected_geometry,invalid_requests_rejected=guard_checks,source_keys_seen=len(last) if 'last' in globals() else len({entry[0] for entry in seen}),owned_after_core_close=True,rom_state_sha256=before,build_report_sha256=sha(out/'motion-build-report.json'),dll_sha256=sha(out/'model-motion.dll'),test_source_sha256=sha(Path(__file__)),core_sha256=sha(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'),live_integration=False,full_scene_60fps=False,remaining_domains=['roads','walls','sky','visibility','HUD/discrete ownership','live scheduling'])
report['rejected_pair_changed_regions']=changed_regions;report['near_plane_recomputed_triangle_vertices']=near_counts;report['material_transition_pairs']=material_transition_pairs;report['materials_discrete_older_until_exact_newer_endpoint']=True
(out/'motion-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
