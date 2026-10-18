"""Read-only original racing-state native source availability and RAM audit."""
from pathlib import Path
import ctypes as C,json,hashlib,struct,os
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().replace("[b'NF_CAPTURE_MODEL_VIEWS'","[b'NF_TEST_EXACT_QUERY_SAMPLE',b'NF_TEST_SAMPLED_ROOT_SELECTION',b'NF_TEST_MOTION_CAPTURE_PROFILE',b'NF_CAPTURE_MODEL_VIEWS'").split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
state=p.parent/'race.state';before=hashlib.sha256(state.read_bytes()).hexdigest();rom=Path(session['rom']).read_bytes()
for flag in [b'NF_TEST_EXACT_QUERY_SAMPLE',b'NF_TEST_SAMPLED_ROOT_SELECTION',b'NF_TEST_MOTION_CAPTURE_PROFILE',b'NF_TEST_MODEL_TEXTURE_TRANSITION',b'NF_TEST_RACING_OWNED_CAPTURE',b'NF_CAPTURE_RETAINED_STRIP',b'NF_CAPTURE_INDEXED_COPY',b'NF_TEST_SURFACE_COMMAND_REUSE_VERIFY',b'NF_TEST_ROAD_COMMAND_REUSE_VERIFY']:assert crt._putenv_s(flag,b'1')==0
for flag in [b'NF_LAYER_DIRTY',b'NF_VERIFY_LAYER_DIRTY',b'NF_TEST_DIRECT_CAPTURE_RAM',b'NF_TEST_VERIFY_CAPTURE_RAM']:
 if os.environ.get(flag.decode())=='1':assert crt._putenv_s(flag,b'1')==0
get=d.nf_live_completed_road_bundle;get.argtypes=[C.c_uint64,U,P,P];d.nf_live_ordered_bundle_free.argtypes=[P];d.nf_dump.argtypes=[C.c_char_p,U,U];d.nf_read.argtypes=[U,C.c_int]
generation_copy=d.nf_page_write_audit_generation_copy;generation_copy.argtypes=[P];display_generation=d.nf_layer_queue_page_generation;display_generation.argtypes=[C.c_uint64,U,U,P]
@Sink
def sink(ctx,e,data,size):
 raw=C.string_at(data,32);serial,begin,end,page=struct.unpack_from('<4I',raw,16);generation=(C.c_uint64*2)();assert generation_copy(generation);latest.update(epoch=e,serial=serial,begin=begin,end=end,page=page,generation=generation[page]);return 1
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(str(state).encode(),0)
d.nf_live_completed_draw_root_commands.argtypes=[C.c_uint64,U,U,P,U,P];d.nf_live_prepared_command_detail.argtypes=[P]
detail_get=d.nf_live_completed_capture_detail;detail_get.argtypes=[C.c_uint64,U,P]
d.nf_live_completed_operation_order.argtypes=[C.c_uint64,U,P,U,P];d.nf_live_completed_ordered_bundle.argtypes=[C.c_uint64,U,P,P];d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P]
seen=set();sources=[];ledger=[];modes=set();display_candidates=[];stable_sequence=[]
try:
 d.nf_page_write_audit_enable(1);d.nf_page_write_audit_generation_reset()
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_bitmap_text_enable(1);assert d.nf_layer_queue_enable(1)
 for frame in range(300):
  key=1|(32 if 180<=frame<240 else 16 if frame>=240 else 0);ledger.append(key);d.nf_frame(key);modes.add((d.nf_read(0x03005f14,4),d.nf_read(0x03006710,1)))
  e,s=latest.get('epoch'),latest.get('serial')
  if e:
   candidate=C.c_uint64();refresh=8242+frame;valid=bool(display_generation(e,refresh,latest['page'],C.byref(candidate)));display_candidates.append(dict(serial=s,refresh=refresh,completion_end=latest['end'],page=latest['page'],completion_generation=latest['generation'],display_generation=candidate.value,uniform=valid,verified=valid and candidate.value==latest['generation']))
  if e and display_candidates[-1]['verified'] and refresh==latest['end']+1:
   hud_get=d.nf_layer_queue_hud_row;hud_get.argtypes=[C.c_uint64,U,U,P,U];text_get=d.nf_layer_queue_text_row;text_get.argtypes=[C.c_uint64,U,U,P,P,U];pages=set();text_valid=True;covered=0;display_valid=True
   for y in range(160):
    row=C.create_string_buffer(34944);indices=C.create_string_buffer(240);coverage=C.create_string_buffer(240);assert hud_get(e,refresh,y,row,34944);assert struct.unpack_from('<2I',row.raw)==(refresh,y)
    display=struct.unpack_from('<H',row.raw,8)[0];pages.add((display>>4)&1);display_valid=display_valid and (display&0x8080)==0 and (display&7)==4 and ((display>>4)&1)==latest['page']
    text_ok=bool(text_get(e,refresh,y,indices,coverage,240));text_valid=text_valid and text_ok
    if text_ok:assert max(coverage.raw)<=1;covered+=sum(coverage.raw)
   stable_sequence.append(dict(epoch=e,serial=s,completion_refresh=latest['end'],display_refresh=refresh,page=latest['page'],display_pages=sorted(pages),display_valid=display_valid,text_valid=text_valid,covered_pixels=covered))
  if e and s in [1,68,69] and display_candidates[-1]['verified'] and refresh==latest['end']+1:
   hud_get=d.nf_layer_queue_hud_row;hud_get.argtypes=[C.c_uint64,U,U,P,U];text_get=d.nf_layer_queue_text_row;text_get.argtypes=[C.c_uint64,U,U,P,P,U];rows=[];texts=[];masks=[];pages=[]
   for y in range(160):
    row=C.create_string_buffer(34944);indices=C.create_string_buffer(240);coverage=C.create_string_buffer(240)
    assert hud_get(e,refresh,y,row,34944) and text_get(e,refresh,y,indices,coverage,240)
    assert struct.unpack_from('<2I',row.raw)==(refresh,y)
    display=struct.unpack_from('<H',row.raw,8)[0];pages.append((display>>4)&1);rows.append(row.raw);texts.append(indices.raw);masks.append(coverage.raw)
   d.nf_pixels.restype=P;(p/('race-stable-'+str(s)+'-original.rgba')).write_bytes(C.string_at(d.nf_pixels(),240*160*4))
   prefix=p/('race-stable-'+str(s));Path(str(prefix)+'-hud.bin').write_bytes(b''.join(rows));Path(str(prefix)+'-text.bin').write_bytes(struct.pack('<8I',0x5854464e,1,e&0xffffffff,e>>32,refresh,240,160,38400)+b''.join(texts)+b''.join(masks));Path(str(prefix)+'-proof.bin').write_bytes(struct.pack('<3Q4I',e,latest['generation'],candidate.value,s,latest['end'],refresh,latest['page']));display_candidates[-1]['display_pages']=sorted(set(pages));display_candidates[-1]['text_covered_pixels']=sum(b''.join(masks))
  if not e or (e,s) in seen:continue
  seen.add((e,s));ptr=P();size=Z();ok=bool(get(e,s,C.byref(ptr),C.byref(size)))
  detail=(U*8)();detail_ok=bool(detail_get(e,s,detail));command_bytes=C.create_string_buffer(144*3604);command_count=U();commands_ok=bool(d.nf_live_completed_draw_root_commands(e,s,0,command_bytes,144,C.byref(command_count)));planner=(U*18)();d.nf_live_scene_planner_detail(planner);rejection=(U*8)();d.nf_live_prepared_command_detail(rejection);kinds=[struct.unpack_from('<I',command_bytes.raw,i*3604)[0] for i in range(command_count.value)] if commands_ok else [];sources.append(dict(refresh=frame+1,epoch=e,serial=s,accepted=ok,bytes=size.value,capture_detail=list(detail) if detail_ok else None,commands_accepted=commands_ok,command_kinds=kinds,command_detail=list(rejection),planner_detail=list(planner)))
  if s in [23,24]:
   q=P();qn=Z();cameras=C.create_string_buffer(144*56);nc=U();assert d.nf_live_completed_draw_scene_packet(e,s,C.byref(q),C.byref(qn),cameras,144,C.byref(nc));(p/('race-identity-'+str(s)+'.nsp')).write_bytes(C.string_at(q,qn.value));d.nf_scene_packet_free.argtypes=[P];d.nf_scene_packet_free(q)
  if s==24:
   transition=d.nf_live_completed_draw_scene_packet_transition;transition.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P]
   def packet_ids(raw):
    _,offset,length=struct.unpack_from('<3I',raw,80);section=raw[offset:offset+length];count=struct.unpack_from('<I',section,4)[0];return [section[8+i*20:28+i*20] for i in range(count)]
   endpoint_ids=set(packet_ids((p/'race-identity-23.nsp').read_bytes())+packet_ids((p/'race-identity-24.nsp').read_bytes()));samples=[]
   for alpha in [0.0,.25,.5,.75,1.0]:
    q=P();qn=Z();cameras=C.create_string_buffer(144*56);nc=U();assert transition(e,23,24,alpha,C.byref(q),C.byref(qn),cameras,144,C.byref(nc));raw=C.string_at(q,qn.value);d.nf_scene_packet_free(q);identities=packet_ids(raw);assert len(identities)==len(set(identities)) and all(x in endpoint_ids for x in identities);samples.append(dict(alpha=alpha,identities=len(identities),cameras=nc.value,duplicates=0,all_endpoint_owned=True))
    if alpha==.5:(p/'race-identity-23-24-sample.nsp').write_bytes(raw)
   (p/'racing-queue-count-alpha-checks.json').write_text(json.dumps(samples,indent=2))

  dispatch_rows=(U*(257*6))();dispatch_count=U();dispatch_get=d.nf_live_completed_dispatch;dispatch_get.argtypes=[C.c_uint64,U,U,U,P,U,P]
  origin_get=d.nf_live_completed_surface_origin;origin_get.argtypes=[C.c_uint64,U,U,U,U,P];bound_get=d.nf_live_completed_surface_bounds;bound_get.argtypes=[C.c_uint64,U,U,U,U,P]
  witnessed=[]
  if dispatch_get(e,s,latest['begin'],latest['end'],dispatch_rows,257,C.byref(dispatch_count)):
   for i in range(dispatch_count.value):
    row=list(dispatch_rows[i*6:(i+1)*6])
    if row[0]==3:continue
    origin=(U*12)();clip=(C.c_uint16*4)();assert origin_get(e,s,latest['begin'],latest['end'],row[1],origin) and bound_get(e,s,latest['begin'],latest['end'],row[1],clip)
    witnessed.append(dict(kind=row[0],source=row[2],ordinal=row[1],origin=list(origin),clip=list(clip)))
  groups=[]
  for key in sorted({(x['kind'],x['source']) for x in witnessed}):
   records=[x for x in witnessed if (x['kind'],x['source'])==key]
   if len(records)>1:groups.append(dict(kind=key[0],source=key[1],records=records,distinct_record_and_clip=len({tuple(x['origin'][2:6]+x['clip']) for x in records})==len(records)))
  sources[-1]['original_draw_witness']=dict(draw_count=len(witnessed),repeated_asset_groups=groups)
  if s in [16,17,64,65]:
   ram_get=d.nf_live_completed_builder_ram;ram_get.argtypes=[C.c_uint64,U,U,P,Z,P];ram=C.create_string_buffer(0x48000);state_address=U();assert ram_get(e,s,0,ram,0x48000,C.byref(state_address))
   path=p/('oracle-builder-'+str(s)+'.bin');path.write_bytes(ram.raw);sources[-1]['builder_oracle_fixture']=dict(path=str(path),state_address=state_address.value,sha256=hashlib.sha256(ram.raw).hexdigest(),epoch=e,serial=s,pass_index=0)
   unchanged=C.create_string_buffer(b'\xa5'*0x48000);negative_state=U(0xabcdef);assert not ram_get(e+1,s,0,unchanged,0x48000,C.byref(negative_state)) and unchanged.raw[:0x48000]==b'\xa5'*0x48000 and negative_state.value==0xabcdef
  query_trace=(U*22)();d.nf_original_query_trace.argtypes=[P];d.nf_original_query_trace(query_trace);sources[-1]['original_query_trace']=list(query_trace)
  owned_query=(U*22)();d.nf_original_query_owned.argtypes=[C.c_uint64,U,U,P];owned_ok=bool(d.nf_original_query_owned(e,s,0x030000c0,owned_query));sources[-1]['owned_query_accepted']=owned_ok;sources[-1]['owned_query_trace']=list(owned_query) if owned_ok else None
  builder_query=(U*14)();d.nf_live_completed_builder_query.argtypes=[C.c_uint64,U,U,P];builder_owned=bool(d.nf_live_completed_builder_query(e,s,0,builder_query));sources[-1]['builder_query_owned']=builder_owned
  if builder_owned:sources[-1]['builder_query_words']=list(builder_query);sources[-1]['builder_matches_latest_query']=owned_ok and list(builder_query)==list(owned_query)[6:8]+list(owned_query)[10:]
  if builder_owned:
   builder_view=(U*12)();d.nf_live_completed_builder_view.argtypes=[C.c_uint64,U,U,P];assert d.nf_live_completed_builder_view(e,s,0,builder_view)
   signed_builder=lambda x:x if x<0x80000000 else x-0x100000000
   qb=list(builder_query)[2:];bv=list(builder_view)
   assert [qb[j*3+i] for i in range(3) for j in range(3)]==bv[:9]
   expected=[-(signed_builder(builder_query[0])//256),-(signed_builder(builder_query[1])//256)]
   assert expected==[signed_builder(bv[9]),signed_builder(bv[11])]
   negative=(U*14)(*([0xabc123]*14));assert not d.nf_live_completed_builder_query(e+1,s,0,negative) and list(negative)==[0xabc123]*14
   sources[-1]['builder_query_view_contract_verified']=True
  if owned_ok:
   assert list(owned_query)[1:4]==[e&0xffffffff,e>>32,s]
   captured_view=(U*12)();d.nf_live_completed_draw_view.argtypes=[C.c_uint64,U,U,P];assert d.nf_live_completed_draw_view(e,s,0,captured_view)
   signed=lambda x:x if x<0x80000000 else x-0x100000000
   base=[signed(owned_query[6]),signed(owned_query[7])];view=list(captured_view);query=list(owned_query)[10:]
   transpose=[query[j*3+i] for i in range(3) for j in range(3)]
   sources[-1]['query_view_contract']=dict(base_q8=base,view_words=view,rotation_transpose_exact=transpose==view[:9],base_floor_translation_exact=[-(base[0]//256),-(base[1]//256)]==[signed(view[9]),signed(view[11])],fractional_q8=[x%256 for x in base])
   assert sources[-1]['query_view_contract']['rotation_transpose_exact'] and sources[-1]['query_view_contract']['base_floor_translation_exact']
   wrong=(U*22)(*([0xabcdef]*22));assert not d.nf_original_query_owned(e+1,s,0x030000c0,wrong) and list(wrong)==[0xabcdef]*22
  if s in [17,65]:
   transition=d.nf_live_completed_draw_scene_packet_transition;transition.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P]
   diagnostic=d.nf_live_completed_draw_sample_detail;diagnostic.argtypes=[P]
   checks=[]
   for tick in range(101):
    pose=(U*26)();d.nf_live_completed_builder_query_sample.argtypes=[C.c_uint64,U,U,U,C.c_double,P];assert d.nf_live_completed_builder_query_sample(e,s-1,s,0,tick/100,pose)
    signed_pose=lambda x:x if x<0x80000000 else x-0x100000000
    assert [-(signed_pose(pose[0])//256),-(signed_pose(pose[1])//256)]==[signed_pose(pose[23]),signed_pose(pose[25])]
    assert [pose[2+j*3+i] for i in range(3) for j in range(3)]==list(pose)[14:23]
    alpha=tick/100;q=P();qn=Z();cameras=C.create_string_buffer(144*56);nc=U()
    accepted=bool(transition(e,s-1,s,alpha,C.byref(q),C.byref(qn),cameras,144,C.byref(nc)))
    detail=(U*8)();diagnostic(detail)
    bounds=(U*9)();d.nf_live_completed_draw_sample_bounds.argtypes=[P];d.nf_live_completed_draw_sample_bounds(bounds)
    guard=(U*6)();d.nf_assembly_bounds_rejection.argtypes=[P];d.nf_assembly_bounds_rejection(guard)
    trace=(U*8)();d.nf_model_classification_trace.argtypes=[P];d.nf_model_classification_trace(trace)
    dispatch=(U*8)();d.nf_model_dispatch_trace.argtypes=[P];d.nf_model_dispatch_trace(dispatch)
    visits=(U*(1+2048*3))();d.nf_scene_command_plan_visits.argtypes=[P];d.nf_scene_command_plan_visits(visits)
    visit_rows=[list(visits[1+i*3:4+i*3]) for i in range(min(visits[0],2048))]
    queue=(U*513)();d.nf_prepared_queue_trace.argtypes=[P];d.nf_prepared_queue_trace(queue)
    root_trace=(U*4)();d.nf_sampled_root_trace.argtypes=[P];d.nf_sampled_root_trace(root_trace)
    checks.append(dict(root_trace=list(root_trace),queue_regions=list(queue[1:1+queue[0]]),object_visits=visit_rows,dispatch_trace=list(dispatch),model_trace=list(trace),guard=list(guard),alpha=alpha,accepted=accepted,bytes=qn.value,cameras=nc.value,detail=list(detail),bounds=list(bounds)))
    if accepted:
     raw=C.string_at(q,qn.value);d.nf_scene_packet_free(q)
     _,offset,length=struct.unpack_from('<3I',raw,80);section=raw[offset:offset+length];amount=struct.unpack_from('<I',section,4)[0]
     identities=[section[8+i*20:28+i*20] for i in range(amount)]
     assert amount==nc.value;checks[-1]['duplicate_identities']=len(identities)-len(set(identities));checks[-1]['duplicate_identity_rows']=[dict(identity=list(struct.unpack('<5I',identity)),positions=[i for i,x in enumerate(identities) if x==identity]) for identity in set(identities) if identities.count(identity)>1]
     checks[-1]['identity_count']=amount
     trailer=8+amount*20;tag,bounded=struct.unpack_from('<2I',section,trailer)
     assert tag in [0x3142464e,0x3242464e]
     clips=[list(struct.unpack_from('<4H',section,trailer+16+i*8)) for i in range(bounded)]
     occurrences=(U*1873)();d.nf_command_occurrence_trace.argtypes=[P];d.nf_command_occurrence_trace(occurrences)
     owned=(U*1873)();owned_count=U();owned_get=d.nf_live_completed_draw_occurrences_sample;owned_get.argtypes=[C.c_uint64,U,U,U,C.c_double,P,U,P]
     assert owned_get(e,s-1,s,0,alpha,owned,1873,C.byref(owned_count)) and list(owned)==list(occurrences) and owned_count.value==owned[0]
     sentinel=(U*1873)(*([0xa5a5a5a5]*1873));sentinel_count=U(0xa5a5a5a5)
     assert not owned_get(e+1,s-1,s,0,alpha,sentinel,1873,C.byref(sentinel_count)) and all(x==0xa5a5a5a5 for x in sentinel) and sentinel_count.value==0xa5a5a5a5
     checks[-1]['owned_occurrence_copy_verified']=True;checks[-1]['wrong_epoch_occurrence_atomic_rejection']=True
     command_rows=[list(owned[1+i*13:14+i*13]) for i in range(owned[0])]
     for duplicate in checks[-1]['duplicate_identity_rows']:
      duplicate['command_records']=[x for x in command_rows if x[0]==duplicate['identity'][0] and x[1]==duplicate['identity'][2]]
      duplicate['clips']=[clips[i] for i in duplicate['positions']]
      duplicate['distinct_clips']=len({tuple(x) for x in duplicate['clips']})==len(duplicate['clips'])
      provenance=[tuple(x[2:]) for x in duplicate['command_records']]
      assert len(provenance)==len(duplicate['positions']) and len(set(provenance))==len(provenance)
      duplicate['distinct_native_provenance']=True
      corrupted=provenance+[provenance[0]];assert len(set(corrupted))!=len(corrupted)
      duplicate['copied_occurrence_negative_rejected']=True
     if alpha in [0,1]:
      exact=P();exact_n=Z();exact_c=C.create_string_buffer(144*56);exact_count=U()
      assert d.nf_live_completed_draw_scene_packet(e,s if alpha==1 else s-1,C.byref(exact),C.byref(exact_n),exact_c,144,C.byref(exact_count))
      assert raw==C.string_at(exact,exact_n.value);d.nf_scene_packet_free(exact)
      checks[-1]['exact_endpoint_bytes']=True
   (p/('racing-bounds-sweep-'+str(s-1)+'-'+str(s)+'.json')).write_text(json.dumps(checks,indent=2))
  if s in [59,60]:
   asset_get=d.nf_live_completed_draw_model_indexed_asset;asset_get.argtypes=[C.c_uint64,U,U,P,P];asset=P();asset_size=Z();assert asset_get(e,s,0,C.byref(asset),C.byref(asset_size));(p/('race-model-'+str(s)+'.bin')).write_bytes(C.string_at(asset,asset_size.value));d.nf_surface_free.argtypes=[P];d.nf_surface_free(asset)
  if s==60:
   sample_asset=d.nf_live_completed_draw_model_sample_asset;sample_asset.argtypes=[C.c_uint64,U,U,U,C.c_double,P,P]
   for alpha in [0.0,0.5,1.0]:
    q=P();qn=Z();assert sample_asset(e,59,60,0,alpha,C.byref(q),C.byref(qn));raw=C.string_at(q,qn.value);d.nf_surface_free(q);basis=(p/('race-model-'+str(60 if alpha==1 else 59)+'.bin')).read_bytes();assert len(raw)==len(basis)
    if alpha in [0,1]:assert raw==basis
    else:assert raw[:40]==basis[:40] and raw[160:]==basis[160:]
   sources[-1]['texture_transition_endpoint_and_owned_material_checks']=3
  if ok and s in [1,68,69]:
   d.nf_pixels.restype=P;(p/('race-source-'+str(s)+'-original.rgba')).write_bytes(C.string_at(d.nf_pixels(),240*160*4))
   (p/('race-source-'+str(s)+'.nfrb')).write_bytes(C.string_at(ptr,size.value))
   hud_get=d.nf_layer_queue_hud_row;hud_get.argtypes=[C.c_uint64,U,U,P,U];row=C.create_string_buffer(34944);palettes=[];hud_rows=[];text_rows=[];coverage_rows=[];missing_text=[]
   text_get=d.nf_layer_queue_text_row;text_get.argtypes=[C.c_uint64,U,U,P,P,U]
   for y in range(160):
    assert hud_get(e,8242+frame,y,row,34944)
    assert struct.unpack_from("<2I",row.raw)==(8242+frame,y)
    palettes.append(row.raw[32896:33408]);hud_rows.append(row.raw);indices=C.create_string_buffer(240);coverage=C.create_string_buffer(240);text_ok=bool(text_get(e,8242+frame,y,indices,coverage,240));missing_text.extend([] if text_ok else [y]);text_rows.append(indices.raw);coverage_rows.append(coverage.raw)
   (p/('race-source-'+str(s)+'-palette.bin')).write_bytes(b''.join(palettes))
   (p/('race-source-'+str(s)+'-hud.bin')).write_bytes(b''.join(hud_rows));sources[-1]['missing_text_rows']=missing_text
   if not missing_text:(p/('race-source-'+str(s)+'-text.bin')).write_bytes(struct.pack('<8I',0x5854464e,1,e&0xffffffff,e>>32,8242+frame,240,160,38400)+b''.join(text_rows)+b''.join(coverage_rows))
   current=C.c_uint64();generation_ok=bool(display_generation(e,8242+frame,latest['page'],C.byref(current)))
   sources[-1]['display_proof']=dict(refresh=8242+frame,page=latest['page'],completion_generation=latest['generation'],display_generation=current.value,verified=generation_ok and current.value==latest['generation'])
   (p/('race-source-'+str(s)+'-proof.bin')).write_bytes(struct.pack('<3Q4I',e,latest['generation'],current.value,s,latest['end'],8242+frame,latest['page']))

  if ok and s==68:
   ordered_ptr=P();ordered_size=Z();assert d.nf_live_completed_ordered_bundle(e,s,C.byref(ordered_ptr),C.byref(ordered_size));raw=C.string_at(ordered_ptr,ordered_size.value);d.nf_live_ordered_bundle_free(ordered_ptr)
   validate=d.nf_live_ordered_bundle_validate;validate.argtypes=[P,Z];assert validate(raw,len(raw));h=struct.unpack_from('<16I',raw);last=h[9]+(h[6]-1)*32;assert struct.unpack_from('<I',raw,last+8)[0]==3
   for offset,value in [(last+12,2),(last+16,0),(last+24,0)]:
    malformed=bytearray(raw);struct.pack_into('<I',malformed,offset,value);assert not validate(bytes(malformed),len(malformed))
   sources[-1]['post_model_order_malformed_rejections']=3
  if not ok:
   events=C.create_string_buffer(608*32);event_count=U();order_ok=bool(d.nf_live_completed_operation_order(e,s,events,608,C.byref(event_count)))
   scene_ptr=P();scene_size=Z();cameras=C.create_string_buffer(144*56);camera_count=U();scene_ok=bool(d.nf_live_completed_draw_scene_packet(e,s,C.byref(scene_ptr),C.byref(scene_size),cameras,144,C.byref(camera_count)))
   if scene_ok:d.nf_scene_packet_free(scene_ptr)
   ordered_ptr=P();ordered_size=Z();ordered_ok=bool(d.nf_live_completed_ordered_bundle(e,s,C.byref(ordered_ptr),C.byref(ordered_size)))
   if ordered_ok:d.nf_live_ordered_bundle_free(ordered_ptr)
   order_detail=(U*8)();d.nf_live_operation_order_detail(order_detail);sources[-1]['order_detail']=list(order_detail)
   sources[-1]['rejection_stages']=dict(order=order_ok,events=event_count.value,scene=scene_ok,cameras=camera_count.value,ordered=ordered_ok)
  if ok:d.nf_live_ordered_bundle_free(ptr)
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:d.nf_dump(str(p/('race-source-audit-'+name+'.bin')).encode(),address,size)
finally:d.nf_close()
baseline=C.CDLL(str(p.parent/'nfsprobe.dll'));baseline.nf_init.argtypes=[C.c_char_p]*2;baseline.nf_state.argtypes=[C.c_char_p,C.c_int];baseline.nf_dump.argtypes=[C.c_char_p,U,U]
assert baseline.nf_init(session['rom'].encode(),b'') and baseline.nf_state(str(state).encode(),0)
try:
 for key in ledger:baseline.nf_frame(key)
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  target=p/('race-source-audit-baseline-'+name+'.bin');baseline.nf_dump(str(target).encode(),address,size);assert target.read_bytes()==(p/('race-source-audit-'+name+'.bin')).read_bytes()
finally:baseline.nf_close()
assert hashlib.sha256(state.read_bytes()).hexdigest()==before
source_by_serial={x['serial']:x for x in sources}
assert len(stable_sequence)==len(sources) and len({x['serial'] for x in stable_sequence})==len(sources)
assert all(x['display_valid'] and x['text_valid'] and x['display_refresh']==x['completion_refresh']+1 for x in stable_sequence)
for x in stable_sequence:x['complete_source']=source_by_serial[x['serial']]['accepted']
report=dict(result='MEASURED',updates=len(ledger),modes=sorted(modes),native_completions=len(sources),accepted=sum(x['accepted'] for x in sources),sources=sources,display_candidates=display_candidates,stable_sequence=stable_sequence,original_ram_exact=True,state_unchanged=True,scope='Saved racing checkpoint native-source availability only; no playable native racing or 60fps proof')
(p/'race-source-availability.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
