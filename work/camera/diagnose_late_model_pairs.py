"""Replay original input ledger and locate exact model material pair changes."""
import ctypes as C,csv,json,struct,hashlib
from pathlib import Path
from project_paths import load_session
p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-59aee71d90ee4c88a494da1a6b97ea61'
session=load_session(Path(str(prefix)+'-session.json'))
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
for k in [b'NF_CAPTURE_MODEL_VIEWS',b'NF_CAPTURE_WALL_OUTPUT_INDICES',b'NF_TEST_INDEXED_ENTRANTS']:assert crt._putenv_s(k,b'1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_scene_packet_free.argtypes=[P]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);latest={}
@Sink
def sink(ctx,e,data,size):latest.update(epoch=e,serial=struct.unpack_from('<I',C.string_at(data,20),16)[0]);return 1
d.nf_native_scene_sink.argtypes=[Sink,P]
pair=d.nf_live_completed_draw_model_pose_pair;pair.argtypes=[C.c_uint64,U,U,P,P,P,P,U,P]
asset=d.nf_live_completed_draw_model_indexed_asset;asset.argtypes=[C.c_uint64,U,U,P,P]
projection=d.nf_live_completed_draw_projection;projection.argtypes=[C.c_uint64,U,U,P]
root=d.nf_live_completed_draw_root;root.argtypes=[C.c_uint64,U,U,P,P]
commands_view=d.nf_live_completed_draw_root_commands_view;commands_view.argtypes=[C.c_uint64,U,U,P,P,U,P]
builder_focal=d.nf_live_completed_draw_builder_focal;builder_focal.argtypes=[C.c_uint64,U,U,P]
commands_focal=d.nf_live_completed_draw_root_commands_focal;commands_focal.argtypes=[C.c_uint64,U,U,P,U,U,P,U,P]
focal_sample=d.nf_projection_focal_sample;focal_sample.argtypes=[P,P,C.c_double,P]
view_sample=d.nf_visibility_view_sample;view_sample.argtypes=[P,P,C.c_double,P]
sample_asset=d.nf_live_completed_draw_model_sample_asset;sample_asset.argtypes=[C.c_uint64,U,U,U,C.c_double,P,P]
sample_commands=d.nf_live_completed_draw_root_model_commands_sample;sample_commands.argtypes=[C.c_uint64,U,U,U,C.c_double,P,U,P]
sample_scene=d.nf_live_completed_draw_scene_packet_transition;sample_scene.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P]
exact_scene=d.nf_live_completed_draw_scene_packet;exact_scene.argtypes=[C.c_uint64,U,P,P,P,U,P]
def model(epoch,serial):
 out=P();size=Z();assert asset(epoch,serial,0,C.byref(out),C.byref(size))
 try:return C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
def parts(m):
 vertices,faces,corners,w,h=struct.unpack_from('<5I',m,4);geometry=160+vertices*24+faces+corners*18;pixels=w*h
 assert m[geometry+pixels*4:geometry+pixels*4+4]==b'NZI1'
 return dict(header=m[:48],geometry=m[160:geometry],indices=m[geometry+pixels*4+16:])
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
checks=[];previous=None;focal_checks=[];zoom_checks=[]
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));identity=(latest.get('epoch'),latest.get('serial'))
  if not identity[0] or identity==previous:continue
  e,s=identity;values=(U*6)();assert projection(e,s,0,values)
  view=(U*12)();evaluated=C.create_string_buffer(65536);assert root(e,s,0,view,evaluated)
  original=C.create_string_buffer(144*3604);sample=C.create_string_buffer(144*3604);na=U();nb=U()
  builder=U();assert builder_focal(e,s,0,C.byref(builder))
  assert commands_view(e,s,0,view,original,144,C.byref(na)) and commands_focal(e,s,0,view,values[0],builder.value,sample,144,C.byref(nb))
  endpoint_equal=na.value==nb.value and original.raw[:na.value*3604]==sample.raw[:nb.value*3604]
  assert endpoint_equal
  intermediate=None
  if s==23:
   assert commands_focal(e,s,0,view,82,74,sample,144,C.byref(nb))
   model_focals=[struct.unpack_from('<I',sample.raw,j*3604+388)[0] for j in range(nb.value) if struct.unpack_from('<I',sample.raw,j*3604)[0]==5]
   assert model_focals and all(v==82 for v in model_focals)
   intermediate=dict(focal=82,commands=nb.value,model_context_focals=model_focals)
  sentinel=C.create_string_buffer(b'X'*(144*3604));bad=U(999)
  assert not commands_focal(e,s,0,view,0,builder.value,sentinel,144,C.byref(bad)) and sentinel.raw[:144*3604]==b'X'*(144*3604) and bad.value==999
  focal_checks.append(dict(serial=s,endpoint_commands_exact=endpoint_equal,root_focal=values[0],builder_focal=builder.value,invalid_focal_atomic=True,intermediate=intermediate))
  if previous:
   e,s=identity;old=previous[1];poses=[C.create_string_buffer(224) for _ in range(4)];count=U()
   accepted=bool(pair(e,old,s,*poses,4,C.byref(count)));a=parts(model(e,old));b=parts(model(e,s))
   original_projection=[]
   for serial,material in [(old,a),(s,b)]:
    values=(U*6)();assert projection(e,serial,0,values)
    assert values[0]==values[1]==values[2]==struct.unpack_from('<d',material['header'],40)[0]
    original_projection.append(list(values))
   checks.append(dict(older=old,newer=s,pose_pair_accepted=accepted,header_exact=a['header']==b['header'],old_projection=list(struct.unpack_from('<3d',a['header'],24)),new_projection=list(struct.unpack_from('<3d',b['header'],24)),geometry_uv_exact=a['geometry']==b['geometry'],indices_exact=a['indices']==b['indices'],index_differences=sum(x!=y for x,y in zip(a['indices'],b['indices'])),old_index_sha256=hashlib.sha256(a['indices']).hexdigest(),new_index_sha256=hashlib.sha256(b['indices']).hexdigest()))
   checks[-1]['owned_root_model_projection']=original_projection
   if a['geometry']==b['geometry'] and a['indices']==b['indices'] and original_projection[0][0]!=original_projection[1][0]:
    views=[];endpoints=[]
    for serial,proj in zip([old,s],original_projection):
     source_view=(U*12)();assert root(e,serial,0,source_view,evaluated);views.append(source_view)
     source_builder=U();assert builder_focal(e,serial,0,C.byref(source_builder));endpoints.append((U*2)(proj[0],source_builder.value))
    for alpha in [0.,.25,.5,.75,1.]:
     focals=(U*2)();sample_view=(U*12)();assert focal_sample(*endpoints,alpha,focals) and view_sample(*views,alpha,sample_view)
     assert list(focals)==[int((1-alpha)*endpoints[0][i]+alpha*endpoints[1][i]+.5) for i in range(2)]
     serial=s if alpha==1 else old;output=C.create_string_buffer(144*3604);amount=U()
     assert commands_focal(e,serial,0,sample_view,*focals,output,144,C.byref(amount))
     model_focals=[struct.unpack_from('<I',output.raw,j*3604+388)[0] for j in range(amount.value) if struct.unpack_from('<I',output.raw,j*3604)[0]==5]
     assert model_focals and all(v==focals[0] for v in model_focals)
     if crt.getenv(b'NF_TEST_FOCAL_SAMPLE'):
      owned=P();length=Z();assert sample_asset(e,old,s,0,alpha,C.byref(owned),C.byref(length))
      try:data=C.string_at(owned,length.value)
      finally:d.nf_scene_packet_free(owned)
      assert struct.unpack_from('<d',data,40)[0]==focals[0] and parts(data)['geometry']==a['geometry'] and parts(data)['indices']==a['indices']
      if alpha in [0.,1.]:assert data==model(e,serial)
      assert sample_commands(e,old,s,0,alpha,output,144,C.byref(amount))
      actual=[struct.unpack_from('<I',output.raw,j*3604+388)[0] for j in range(amount.value) if struct.unpack_from('<I',output.raw,j*3604)[0]==5]
      assert actual and all(v==focals[0] for v in actual)
      scene=P();length=Z();poses=C.create_string_buffer(144*56);pose_count=U()
      assert sample_scene(e,old,s,alpha,C.byref(scene),C.byref(length),poses,144,C.byref(pose_count)),(old,s,alpha)
      try:packet=C.string_at(scene,length.value)
      finally:d.nf_scene_packet_free(scene)
      sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))}
      assert struct.unpack_from('<d',sections[1],40)[0]==focals[0]
      identities=sections[5];world_count=struct.unpack_from('<I',sections[2],4)[0];order_count=struct.unpack_from('<I',sections[3],4)[0]
      order=struct.unpack_from('<'+str(order_count)+'I',sections[3],8)
      expected=[(struct.unpack_from('<I',output.raw,j*3604)[0],struct.unpack_from('<I',output.raw,j*3604+20)[0]) for j in range(amount.value)]
      expected=[(3 if kind==5 else kind,source) for kind,source in expected]
      actual=[]
      for value in order:
       index=value if value<world_count else world_count+0xffffffff-value
       key=struct.unpack_from('<5I',identities,8+index*20);actual.append((key[0],key[2]))
      assert actual==expected and pose_count.value==order_count
      if alpha in [0.,1.]:
       exact=P();size=Z();exact_poses=C.create_string_buffer(144*56);count=U();assert exact_scene(e,serial,C.byref(exact),C.byref(size),exact_poses,144,C.byref(count))
       try:assert packet==C.string_at(exact,size.value) and poses.raw[:pose_count.value*56]==exact_poses.raw[:count.value*56]
       finally:d.nf_scene_packet_free(exact)
     zoom_checks.append(dict(older=old,newer=s,alpha=alpha,draw_focal=focals[0],builder_focal=focals[1],commands=amount.value,model_context_focals=model_focals))
  previous=identity
finally:d.nf_close()
assert len(zoom_checks)==25
for alpha in [-1.,2.,float('nan'),float('inf')]:
 sentinel=(U*2)(123,456);assert not focal_sample((U*2)(76,68),(U*2)(88,80),alpha,sentinel) and list(sentinel)==[123,456]
assert any(not x['pose_pair_accepted'] for x in checks)
report=dict(result='AUDITED',checks=checks,focal_planner_checks=focal_checks,zoom_checks=zoom_checks,scope='Fresh159 original inputs; dual original-focal cloned planner endpoints exact, five zoom pairs atfive fractions generate matching model-context focal; invalid alpha/focal atomic. Sampled object pose/world asset/GPU integration still incomplete.')
(p/'late-model-pair-diagnostic.json').write_text(json.dumps(report,indent=2));print(json.dumps([x for x in checks if not x['pose_pair_accepted']]))
