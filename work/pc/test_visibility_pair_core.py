from pathlib import Path
import os,ctypes as C,json,hashlib,struct,collections,time
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-visibility-pair-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'pair-build-report.json').read_text());assert receipt['core_sha256']==sha(out/'capture-host.dll')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'));world=C.CDLL(str(base/'NFSUG-pc-world-mesh-motion-tests/world-mesh-motion.dll'));model=C.CDLL(str(base/'NFSUG-pc-model-motion-tests/model-motion.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);pair=fn(d,'nf_pc_visibility_pair',[P,P,C.c_double,P,P,P]);packet_free=fn(d,'nf_scene_packet_free',[P],None);missing=fn(d,'nf_pc_pair_missing_model',[P],None);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None);decode=fn(world,'nf_pc_world_decode',[P,S,S],P);world_free=fn(world,'nf_pc_world_free',[P],None);world_info=fn(world,'nf_pc_world_info',[P,P]);mesh=fn(world,'nf_pc_world_mesh',[P,U,S],P);mesh_free=fn(world,'nf_pc_world_mesh_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;seen=set();previous=None;rows=[];pairs=0
world_buffer=fn(world,'nf_pc_world_mesh_buffer',[P,U,P,P]);world_model=fn(world,'nf_pc_world_model',[P,U,P,P]);model_decode=fn(model,'nf_pc_model_mesh_decode',[P,S,S],P);model_buffer=fn(model,'nf_pc_model_mesh_buffer',[P,U,P,P]);model_free=fn(model,'nf_pc_model_mesh_free',[P],None);midpoint_saved=False;negative_requests=0
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial)
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
     oi=(Q*5)();assert owner_info(frame,owner,oi);key=tuple(oi)
     if key in seen:continue
     seen.add(key);p=P();n=S();assert component(frame,owner,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value)
     if previous and previous[0][0]==oi[0] and previous[0][1]<oi[1] and 0<oi[3]-previous[0][3]<=8:
      ak=(Q*5)(*previous[0]);pairs+=1
      for alpha in [0.,.25,.5,.75,1.]:
       result=P();size=S();stage=U();began=time.perf_counter();ok=pair(ak,oi,alpha,C.byref(result),C.byref(size),C.byref(stage));cost=(time.perf_counter()-began)*1000;after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
       row=dict(older=list(ak),newer=list(oi),alpha=alpha,success=bool(ok),stage=stage.value,ms=cost)
       if ok:
        assert result.value and 92<=size.value<=64*1024*1024;raw=C.string_at(result,size.value);packet_free(result);row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if alpha in [0.,1.]:assert raw==(previous[1] if alpha==0 else packet),('Endpoint mismatch',list(ak),list(oi),alpha)
        w=decode(raw,len(raw),64*1024*1024);assert w,('Paired packet decoder rejected',row);wi=(Q*4)();assert world_info(w,wi);renderable=0;geometry_digest=hashlib.sha256();model_vertices=0
        for surface in range(wi[0]):
         m=mesh(w,surface,32*1024*1024)
         if m:
          renderable+=1;p=P();n=S();assert world_buffer(m,0,C.byref(p),C.byref(n));geometry_digest.update(struct.pack('<Q',n.value));geometry_digest.update(C.string_at(p,n.value));mesh_free(m)
        for mi in range(wi[1]):
         p=P();n=S();assert world_model(w,mi,C.byref(p),C.byref(n));m=model_decode(p,n,32*1024*1024);assert m,('Paired model rejected',row,mi);assert model_buffer(m,0,C.byref(p),C.byref(n));geometry_digest.update(struct.pack('<Q',n.value));geometry_digest.update(C.string_at(p,n.value));model_vertices+=n.value//20;model_free(m)
        world_free(w);row.update(surfaces=wi[0],models=wi[1],renderable_world_meshes=renderable,projected_geometry_sha256=geometry_digest.hexdigest(),model_triangle_vertices=model_vertices)
        if alpha==.5 and not midpoint_saved:(out/'paired-midpoint.nsp').write_bytes(raw);midpoint_saved=True
       else:
        assert not result.value and size.value==0;why=(U*6)();missing(why);row['missing_model_detail']=list(why)
       rows.append(row)
     previous=(key,packet)
   finally:frame_free(frame)
  def rejected(a,b,alpha):
   global negative_requests
   p=P(0x12345678);n=S(4321);stage=U();assert not pair(a,b,alpha,C.byref(p),C.byref(n),C.byref(stage)) and p.value==0x12345678 and n.value==4321;negative_requests+=1
  for alpha in [-1.,2.,float('nan')]:rejected(ak,oi,alpha)
  rejected(oi,ak,.5)
  for field in range(5):
   bad=(Q*5)(*oi);bad[field]+=1;rejected(ak,bad,.5)
  assert load(h,data,len(data));rejected(ak,oi,.5)
finally:rclose(r);close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';assert before=={str(p):sha(p) for p in [rom,state]};assert pairs>20
success=[row for row in rows if row['success']];failed=[row for row in rows if not row['success']];fractions=[row for row in success if 0<row['alpha']<1];endpoints=[row for row in success if row['alpha'] in [0.,1.]]
different=0
for start in range(0,len(rows),5):
 group=rows[start:start+5]
 if all(row['success'] for row in group):different+=sum(row['projected_geometry_sha256'] not in [group[0]['projected_geometry_sha256'],group[4]['projected_geometry_sha256']] for row in group[1:4])
assert different>0
report=dict(result='PARTIAL_EXISTING_PAIRED_VISIBILITY_REGENERATION' if failed else 'PASS_EXISTING_PAIRED_VISIBILITY_REGENERATION_COMPONENT',original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),owners=len(seen),pairs=pairs,requests=len(rows),successes=len(success),successful_exact_endpoints=len(endpoints),successful_fractional_packets=len(fractions),failures=len(failed),failure_stages=dict(collections.Counter(str(row['stage']) for row in failed)),fractional_surface_meshes=sum(row.get('surfaces',0) for row in fractions),fractional_renderable_world_meshes=sum(row.get('renderable_world_meshes',0) for row in fractions),fractional_model_triangle_vertices=sum(row.get('model_triangle_vertices',0) for row in fractions),fractional_projected_geometry_different_from_both_endpoints=different,negative_requests_untouched=negative_requests,reset_stale_owner_rejected=True,midpoint_packet_sha256=sha(out/'paired-midpoint.nsp'),world_decoder_sha256=sha(base/'NFSUG-pc-world-mesh-motion-tests/world-mesh-motion.dll'),model_decoder_sha256=sha(base/'NFSUG-pc-model-motion-tests/model-motion.dll'),no_extra_logic_steps=True,rom_state_sha256=before,core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'pair-build-report.json'),script_sha256=sha(Path(__file__)),rows=rows,live_integration=False,full_scene_60fps=False)
(out/'pair-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
