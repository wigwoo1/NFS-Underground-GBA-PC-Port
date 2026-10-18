"""Actual original replay verifies cache ownership, expiry and epoch rejection."""
import ctypes as C,struct,json,uuid
from pathlib import Path
p=Path(__file__).resolve().parent;P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
crt.getenv.argtypes=[C.c_char_p];crt.getenv.restype=C.c_void_p
for k in ['NF_CAPTURE_MODEL_VIEWS']:assert crt._putenv_s(k.encode(),b'1')==0
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p/'prototype-runs/menu-navigation/quick-1-release.state'
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_dump.argtypes=[C.c_char_p,U,U]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);d.nf_native_scene_sink.argtypes=[Sink,P];latest={}
@Sink
def sink(ctx,e,data,size):latest.update(epoch=e,serial=struct.unpack_from('<I',C.string_at(data,20),16)[0]);return 1
d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P];d.nf_scene_packet_free.argtypes=[P]
def read(e,s):
 out=P();n=Z();poses=C.create_string_buffer(144*56);count=U();assert d.nf_live_completed_draw_scene_packet(e,s,C.byref(out),C.byref(n),poses,144,C.byref(count));return out,n.value,C.string_at(out,n.value),poses.raw[:count.value*56]
def reject(e,s):
 out=P(123);n=Z(999);poses=C.create_string_buffer(b'x'*8064);count=U(888);assert not d.nf_live_completed_draw_scene_packet(e,s,C.byref(out),C.byref(n),poses,144,C.byref(count));assert out.value==123 and n.value==999 and count.value==888 and poses.raw[:8064]==b'x'*8064
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
raw=rom.read_bytes();assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_layer_queue_enable(1)
pair=d.nf_live_completed_draw_camera_pair;pair.argtypes=[C.c_uint64,U,U,P,P,U,P];d.nf_live_completed_draw_root_cameras.argtypes=[C.c_uint64,U,U,P,U,P]
export=p/"prototype-runs"/("sampled-draw-scenes-"+uuid.uuid4().hex);export.mkdir(parents=True)
exports=[]
seen=[];checks=[];transition_checks=[];palette_timelines=[];rejected=0
try:
 for i in range(120):
  d.nf_frame(16 if 90<=i<92 else 0)
  identity=(latest.get('epoch'),latest.get('serial'))
  if not identity[0] or identity in seen:continue
  seen.append(identity)
  if len(seen)<2:continue
  e,s=identity;old=seen[-2][1];a=C.create_string_buffer(b'A'*8064,8064);b=C.create_string_buffer(b'B'*8064,8064);count=U(999)
  ok=pair(e,old,s,a,b,144,C.byref(count))
  transition=d.nf_live_completed_draw_scene_packet_transition;transition.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P]
  transition_results=[]
  for alpha in [0.,.5,1.]:
   packet=P(123);size=Z(999);poses=C.create_string_buffer(b'T'*8064,8064);n=U(888)
   accepted=transition(e,old,s,alpha,C.byref(packet),C.byref(size),poses,144,C.byref(n))
   if accepted:
    if alpha in [0.,1.]:
     exact,exact_size,exact_bytes,exact_poses=read(e,s if alpha==1 else old);assert size.value==exact_size and C.string_at(packet,size.value)==exact_bytes and poses.raw[:n.value*56]==exact_poses;d.nf_scene_packet_free(exact)
    raw=C.string_at(packet,size.value);sections={t:raw[o:o+z] for t,o,z in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))};world_count=struct.unpack_from('<I',sections[2],4)[0];order_count=struct.unpack_from('<I',sections[3],4)[0];order=struct.unpack_from('<'+str(order_count)+'I',sections[3],8);actual=[]
    for value in order:
     index=value if value<world_count else world_count+4294967295-value;key=struct.unpack_from('<5I',sections[5],8+index*20);actual.append((key[0],key[2]))
    planner=d.nf_live_completed_draw_root_model_commands_sample;planner.argtypes=[C.c_uint64,U,U,U,C.c_double,P,U,P];expected=[]
    for ordinal in range(4):
     commands=C.create_string_buffer(144*3604);amount=U()
     if not planner(e,old,s,ordinal,alpha,commands,144,C.byref(amount)):break
     for j in range(amount.value):
      kind=struct.unpack_from('<I',commands.raw,j*3604)[0];source=struct.unpack_from('<I',commands.raw,j*3604+20)[0];expected.append((3 if kind==5 else kind,source))
    assert actual==expected and n.value==len(expected)
    d.nf_scene_packet_free(packet)
   else:assert packet.value==123 and size.value==999 and n.value==888 and poses.raw==b'T'*8064
   detail=(U*8)();d.nf_live_completed_draw_sample_detail(detail);transition_results.append(dict(alpha=alpha,accepted=bool(accepted),commands=n.value if accepted else 0,failure_detail=list(detail) if not accepted else None))
  for epoch,older,newer,alpha,capacity in [(e+1,old,s,.5,144),(e,s,old,.5,144),(e,old,s,float('nan'),144),(e,old,s,.5,143)]:
   packet=P(123);size=Z(999);poses=C.create_string_buffer(b'T'*8064,8064);n=U(888);assert not transition(epoch,older,newer,alpha,C.byref(packet),C.byref(size),poses,capacity,C.byref(n));assert packet.value==123 and size.value==999 and n.value==888 and poses.raw==b'T'*8064
  timeline=d.nf_live_completed_draw_palette_timeline;timeline.argtypes=[C.c_uint64,U,U,P,P,U,P];d.nf_live_completed_draw_timing.argtypes=[C.c_uint64,U,U,P]
  for serial in [old,s]:
   root=C.create_string_buffer(512);draws=C.create_string_buffer(128*528);amount=U();assert timeline(e,serial,0,root,draws,128,C.byref(amount));timing=(U*6)();assert d.nf_live_completed_draw_timing(e,serial,0,timing)
   import hashlib
   rows=[]
   for j in range(amount.value):
    kind,source=struct.unpack_from('<2I',draws.raw,j*528);palette=draws.raw[j*528+8:j*528+520];refresh,vcount=struct.unpack_from('<2I',draws.raw,j*528+520);assert timing[0]<=refresh<=timing[1] and vcount<228
    rows.append(dict(kind=kind,source=source,refresh=refresh,vcount=vcount,palette_sha256=hashlib.sha256(palette).hexdigest(),root_palette_exact=palette==root.raw))
   if not any(x['serial']==serial for x in palette_timelines):palette_timelines.append(dict(serial=serial,root_refresh=timing[0],model_refresh=timing[1],root_palette_sha256=hashlib.sha256(root.raw).hexdigest(),draws=rows))
   badroot=C.create_string_buffer(b'R'*512,512);baddraws=C.create_string_buffer(b'D'*(128*528),128*528);badcount=U(888);assert not timeline(e+1,serial,0,badroot,baddraws,128,C.byref(badcount));assert badroot.raw==b'R'*512 and baddraws.raw==b'D'*(128*528) and badcount.value==888
  transition_checks.append(dict(older=old,newer=s,original_topology_matched=bool(ok),results=transition_results))
  if not ok:assert a.raw==b'A'*8064 and b.raw==b'B'*8064 and count.value==999;rejected+=1;continue
  for serial,actual in [(old,a),(s,b)]:
   expected=b''
   for ordinal in range(16):
    poses=C.create_string_buffer(8064);n=U()
    if not d.nf_live_completed_draw_root_cameras(e,serial,ordinal,poses,144,C.byref(n)):break
    expected+=poses.raw[:n.value*56]
   assert len(expected)==count.value*56 and actual.raw[:len(expected)]==expected
  for epoch,older,newer,cap in [(e+1,old,s,144),(e,s,old,144),(e,old,s,143),(e,old,s+1000,144)]:
   sentinel=U(888);x=C.create_string_buffer(b'X'*8064,8064);y=C.create_string_buffer(b'Y'*8064,8064);assert not pair(epoch,older,newer,x,y,cap,C.byref(sentinel));assert x.raw==b'X'*8064 and y.raw==b'Y'*8064 and sentinel.value==888
  d.nf_live_completed_draw_root.argtypes=[C.c_uint64,U,U,P,P];d.nf_live_completed_draw_root_commands.argtypes=[C.c_uint64,U,U,P,U,P];d.nf_live_completed_draw_root_commands_view.argtypes=[C.c_uint64,U,U,P,P,U,P];d.nf_visibility_view_sample.argtypes=[P,P,C.c_double,P]
  views=[];endpoint_equal=[]
  for serial in [old,s]:
   view=(U*12)();result=C.create_string_buffer(65536);assert d.nf_live_completed_draw_root(e,serial,0,view,result);views.append(view)
   original=C.create_string_buffer(144*3604);recomputed=C.create_string_buffer(144*3604);na=U();nb=U();assert d.nf_live_completed_draw_root_commands(e,serial,0,original,144,C.byref(na));assert d.nf_live_completed_draw_root_commands_view(e,serial,0,view,recomputed,144,C.byref(nb));assert na.value==nb.value and original.raw[:na.value*3604]==recomputed.raw[:nb.value*3604];endpoint_equal.append(True)
  world=d.nf_live_completed_draw_root_world_view;world.argtypes=[C.c_uint64,U,U,U,P,P,P,P,P,P,P,P];d.nf_live_completed_draw_root_asset.argtypes=[C.c_uint64,U,U,U,P,P,P,P];d.nf_live_completed_draw_root_metadata.argtypes=[C.c_uint64,U,U,U,P,P,P]
  asset_checks=0
  for serial,view in zip([old,s],views):
   commands=C.create_string_buffer(144*3604);n=U();assert d.nf_live_completed_draw_root_commands(e,serial,0,commands,144,C.byref(n));selected=[]
   for kind in [1,2]:
    matches=[j for j in range(n.value) if struct.unpack_from('<I',commands.raw,j*3604)[0]==kind]
    if matches:selected.append(matches[0])
   for index in selected:
    outputs=[P(),Z(),P(),Z(),P(),Z(),U()];assert world(e,serial,0,index,view,*[C.byref(v) for v in outputs]);expected=[P(),Z(),P(),Z(),P(),Z(),U()]
    assert d.nf_live_completed_draw_root_asset(e,serial,0,index,*[C.byref(v) for v in expected[:4]]) and d.nf_live_completed_draw_root_metadata(e,serial,0,index,*[C.byref(v) for v in expected[4:]])
    for at in [0,2,4]:assert outputs[at+1].value==expected[at+1].value and C.string_at(outputs[at],outputs[at+1].value)==C.string_at(expected[at],expected[at+1].value)
    assert outputs[6].value==expected[6].value
    for collection in [outputs,expected]:
     for at in [0,2,4]:d.nf_scene_packet_free(collection[at])
    asset_checks+=1
  sampled=(U*12)();assert d.nf_visibility_view_sample(views[0],views[1],.5,sampled);commands=C.create_string_buffer(144*3604);nc=U();sampled_ok=d.nf_live_completed_draw_root_commands_view(e,old,0,sampled,commands,144,C.byref(nc))
  packet_views=d.nf_live_completed_draw_scene_packet_views;packet_views.argtypes=[C.c_uint64,U,P,U,P,P,P,U,P]
  packet_endpoint_checks=0
  for serial in [old,s]:
   pass_views=[]
   for ordinal in range(4):
    view=(U*12)();result=C.create_string_buffer(65536)
    if not d.nf_live_completed_draw_root(e,serial,ordinal,view,result):break
    pass_views.extend(view)
   all_views=(U*len(pass_views))(*pass_views);out=P();size=Z();poses=C.create_string_buffer(8064);n=U()
   assert packet_views(e,serial,all_views,len(pass_views)//12,C.byref(out),C.byref(size),poses,144,C.byref(n))
   exact,exact_size,exact_bytes,exact_poses=read(e,serial)
   assert size.value==exact_size and C.string_at(out,size.value)==exact_bytes and poses.raw[:n.value*56]==exact_poses
   d.nf_scene_packet_free(out);d.nf_scene_packet_free(exact);packet_endpoint_checks+=1
  midpoint_views=[]
  for ordinal in range(len(pass_views)//12):
   pair_views=[]
   for serial in [old,s]:
    view=(U*12)();result=C.create_string_buffer(65536);assert d.nf_live_completed_draw_root(e,serial,ordinal,view,result);pair_views.append(view)
   view=(U*12)();assert d.nf_visibility_view_sample(pair_views[0],pair_views[1],.5,view);midpoint_views.extend(view)
  all_views=(U*len(midpoint_views))(*midpoint_views);out=P(123);size=Z(999);poses=C.create_string_buffer(b'Z'*8064,8064);n=U(888)
  midpoint_packet=packet_views(e,old,all_views,len(midpoint_views)//12,C.byref(out),C.byref(size),poses,144,C.byref(n))
  if midpoint_packet:
   assert size.value>0 and n.value==count.value;d.nf_scene_packet_free(out)
  else:assert out.value==123 and size.value==999 and n.value==888 and poses.raw==b'Z'*8064
  for epoch,serial,view_count,capacity in [(e+1,old,len(midpoint_views)//12,144),(e,old,99,144),(e,old,len(midpoint_views)//12,143),(e,s+1000,len(midpoint_views)//12,144)]:
   out=P(123);size=Z(999);poses=C.create_string_buffer(b'Z'*8064,8064);n=U(888)
   assert not packet_views(epoch,serial,all_views,view_count,C.byref(out),C.byref(size),poses,capacity,C.byref(n))
   assert out.value==123 and size.value==999 and n.value==888 and poses.raw==b'Z'*8064
  model_pair=d.nf_live_completed_draw_model_pose_pair;model_pair.argtypes=[C.c_uint64,U,U,P,P,P,P,U,P];d.nf_live_completed_draw_model_indexed_asset.argtypes=[C.c_uint64,U,U,P,P]
  model_poses=[C.create_string_buffer(b'M'*224,224) for _ in range(4)];model_count=U(888)
  model_ok=model_pair(e,old,s,*model_poses,4,C.byref(model_count))
  model_camera_root_differences=0
  if model_ok:
   assert 0<model_count.value<=4
   for ordinal in range(model_count.value):
    for serial,camera_at,object_at in [(old,0,2),(s,1,3)]:
     asset=P();size=Z();assert d.nf_live_completed_draw_model_indexed_asset(e,serial,ordinal,C.byref(asset),C.byref(size));data=C.string_at(asset,size.value);d.nf_scene_packet_free(asset)
     assert model_poses[camera_at].raw[ordinal*56:(ordinal+1)*56]==data[48:104]
     assert model_poses[object_at].raw[ordinal*56:(ordinal+1)*56]==data[104:160]
     roots=C.create_string_buffer(8064);root_count=U();assert d.nf_live_completed_draw_root_cameras(e,serial,ordinal,roots,144,C.byref(root_count))
     model_camera_root_differences+=data[48:104]!=roots.raw[:56]
  else:assert model_count.value==888 and all(x.raw==b'M'*224 for x in model_poses)
  sampled_model_assets=0;palette_changes=0
  sample_asset=d.nf_live_completed_draw_model_sample_asset;sample_asset.argtypes=[C.c_uint64,U,U,U,C.c_double,P,P]
  if model_ok:
   for ordinal in range(model_count.value):
    endpoint_assets=[]
    for serial in [old,s]:
     asset=P();size=Z();assert d.nf_live_completed_draw_model_indexed_asset(e,serial,ordinal,C.byref(asset),C.byref(size));endpoint_assets.append(C.string_at(asset,size.value));d.nf_scene_packet_free(asset)
    palette_changes+=endpoint_assets[0][160:]!=endpoint_assets[1][160:]
    for alpha in [0.,.5,1.]:
     asset=P();size=Z();assert sample_asset(e,old,s,ordinal,alpha,C.byref(asset),C.byref(size));data=C.string_at(asset,size.value);d.nf_scene_packet_free(asset)
     if alpha in [0.,1.]:assert data==endpoint_assets[int(alpha)]
     else:
      assert data[:48]==endpoint_assets[0][:48] and data[160:]==endpoint_assets[0][160:]
      for offset in [48,104]:
       a=struct.unpack_from('<7d',endpoint_assets[0],offset);b=struct.unpack_from('<7d',endpoint_assets[1],offset);v=struct.unpack_from('<7d',data,offset)
       assert max(abs(v[j]-(a[j]+b[j])*.5) for j in range(3))<1e-12
       assert abs(sum(x*x for x in v[3:])-1)<1e-12
     sampled_model_assets+=1
  for alpha,ordinal in [(float('nan'),0),(-.1,0),(1.1,0),(.5,99)]:
   asset=P(123);size=Z(999);assert not sample_asset(e,old,s,ordinal,alpha,C.byref(asset),C.byref(size));assert asset.value==123 and size.value==999
  model_commands=d.nf_live_completed_draw_root_model_commands_sample;model_commands.argtypes=[C.c_uint64,U,U,U,C.c_double,P,U,P];model_command_checks=0
  if model_ok:
   for ordinal in range(model_count.value):
    for alpha in [0.,.5,1.]:
     commands_out=C.create_string_buffer(144*3604);n=U();assert model_commands(e,old,s,ordinal,alpha,commands_out,144,C.byref(n))
     assert n.value>0
     if alpha in [0.,1.]:
      expected=C.create_string_buffer(144*3604);expected_count=U();assert d.nf_live_completed_draw_root_commands(e,s if alpha==1 else old,ordinal,expected,144,C.byref(expected_count));assert n.value==expected_count.value and commands_out.raw[:n.value*3604]==expected.raw[:n.value*3604]
     model_command_checks+=1
  for alpha,ordinal,capacity in [(float('nan'),0,144),(.5,99,144),(.5,0,143),(-.1,0,144)]:
   commands_out=C.create_string_buffer(b'X'*(144*3604),144*3604);n=U(888);assert not model_commands(e,old,s,ordinal,alpha,commands_out,capacity,C.byref(n));assert n.value==888 and commands_out.raw==b'X'*(144*3604)
  for epoch,older,newer,capacity in [(e+1,old,s,4),(e,s,old,4),(e,old,s,3),(e,old,s+1000,4)]:
   outputs=[C.create_string_buffer(b'M'*224,224) for _ in range(4)];n=U(888)
   assert not model_pair(epoch,older,newer,*outputs,capacity,C.byref(n));assert n.value==888 and all(x.raw==b'M'*224 for x in outputs)
  scene_sample=d.nf_live_completed_draw_scene_packet_sample;scene_sample.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P];scene_sample_checks=0
  for alpha in [0.,.5,1.]:
   out=P();size=Z();poses=C.create_string_buffer(8064);n=U();assert scene_sample(e,old,s,alpha,C.byref(out),C.byref(size),poses,144,C.byref(n))
   assert n.value==count.value
   if alpha in [0.,1.]:
    exact,exact_size,exact_bytes,exact_poses=read(e,s if alpha==1 else old);assert size.value==exact_size and C.string_at(out,size.value)==exact_bytes and poses.raw[:n.value*56]==exact_poses;d.nf_scene_packet_free(exact)
   if not checks:
    name=f'pair-{old}-{s}-alpha-{alpha:g}';packet_path=export/(name+'.bin');camera_path=export/(name+'-cameras.bin');packet_path.write_bytes(C.string_at(out,size.value));camera_path.write_bytes(poses.raw[:n.value*56]);exports.append(dict(epoch=e,older=old,newer=s,alpha=alpha,packet=str(packet_path),cameras=str(camera_path),command_count=n.value))
   d.nf_scene_packet_free(out);scene_sample_checks+=1
  for epoch,older,newer,alpha,capacity in [(e+1,old,s,.5,144),(e,s,old,.5,144),(e,old,s,float('nan'),144),(e,old,s,.5,143)]:
   out=P(123);size=Z(999);poses=C.create_string_buffer(b'X'*8064,8064);n=U(888)
   assert not scene_sample(epoch,older,newer,alpha,C.byref(out),C.byref(size),poses,capacity,C.byref(n));assert out.value==123 and size.value==999 and n.value==888 and poses.raw==b'X'*8064
  midpoint_assets=0;midpoint_rejections=0
  for kind in [1,2]:
   matches=[j for j in range(nc.value) if struct.unpack_from('<I',commands.raw,j*3604)[0]==kind]
   if not matches:continue
   outputs=[P(123),Z(999),P(123),Z(999),P(123),Z(999),U(888)]
   accepted=world(e,old,0,matches[0],sampled,*[C.byref(v) for v in outputs])
   if accepted:
    assert outputs[0].value and outputs[1].value and outputs[4].value and outputs[5].value
    wall_modes=[7,8] if crt.getenv(b'NF_CAPTURE_WALL_OUTPUT_INDICES') else [2,3]
    assert outputs[6].value in ([5,6] if kind==1 else wall_modes)
    for at in [0,2,4]:d.nf_scene_packet_free(outputs[at])
    midpoint_assets+=1
   else:
    assert [v.value for v in outputs]==[123,999,123,999,123,999,888];midpoint_rejections+=1
  for epoch,ordinal,index,view in [(e+1,0,0,sampled),(e,999,0,sampled),(e,0,999,sampled),(e,0,0,None)]:
   outputs=[P(123),Z(999),P(123),Z(999),P(123),Z(999),U(888)]
   assert not world(epoch,old,ordinal,index,view,*[C.byref(v) for v in outputs])
   assert [v.value for v in outputs]==[123,999,123,999,123,999,888]
  checks.append(dict(older=old,newer=s,commands=count.value,exact_independent_root_camera_arrays=True,explicit_endpoint_commands_exact=endpoint_equal,sampled_view_commands_accepted=bool(sampled_ok),sampled_view_commands=nc.value,explicit_endpoint_world_assets_metadata_exact=asset_checks,midpoint_world_assets=midpoint_assets,midpoint_topology_rejections=midpoint_rejections,world_atomic_negative_cases=4,explicit_view_scene_packets_exact=packet_endpoint_checks,midpoint_scene_packet_accepted=bool(midpoint_packet),packet_atomic_negative_cases=4,model_pose_pair_accepted=bool(model_ok),model_pose_pairs=model_count.value if model_ok else 0,model_atomic_negative_cases=4,model_camera_root_differences=model_camera_root_differences,sampled_model_assets=sampled_model_assets,palette_changing_model_pairs=palette_changes,sampled_model_atomic_negative_cases=4,sampled_model_command_checks=model_command_checks,model_command_atomic_negative_cases=4,sampled_complete_scene_checks=scene_sample_checks,sampled_scene_atomic_negative_cases=4))
finally:d.nf_close()
assert any(x["model_pose_pair_accepted"] for x in checks)
assert checks and rejected and sum(x["midpoint_world_assets"] for x in checks)>0
report=dict(result='PASS',palette_timelines=palette_timelines,transition_checks=transition_checks,sample_exports=exports,checks=checks,topology_changes_rejected=rejected,atomic_negative_cases=4*len(checks),scope='Actual retained original draw occurrences match by kind/source/object/owner/pass and state/order; endpoint camera arrays agree with independent root accessor. Fractional native geometry/bounds and live attachment remain separate.')
(p/'draw-camera-pair-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',paired_scenes=len(checks),topology_rejections=rejected,atomic_negative_cases=4*len(checks))))

