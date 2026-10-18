from pathlib import Path
import ctypes as C, struct, json, hashlib,sys
p=Path('work/camera').resolve(); d=C.CDLL(str(p/'visibility-probe-wide.dll'))
P=C.c_void_p; U=C.c_uint32; Z=C.c_size_t
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,U,U]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);d.nf_native_scene_sink.argtypes=[Sink,P]
d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_native_scene_multimodel.argtypes=[C.c_int]
d.nf_live_completed_models_count.argtypes=[C.c_uint64,U,U,U,C.POINTER(U)]
d.nf_live_completed_model_inputs_for.argtypes=[C.c_uint64,U,U,U,P,P]
d.nf_pose_decode.argtypes=[P,P,P]
d.nf_live_completed_native_multimodel_owned.argtypes=[C.c_uint64,U,U,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
d.nf_live_completed_native_multimodel_indexed_owned.argtypes=d.nf_live_completed_native_multimodel_owned.argtypes
d.nf_scene_packet_free.argtypes=[P]
d.nf_live_completed_object_world_rotation.argtypes=[C.c_uint64,U,U,U,U,U,P]
d.nf_live_completed_render_read.argtypes=[C.c_uint64,U,U,U,U,P,Z]
d.nf_live_completed_snapshot_read.argtypes=[C.c_uint64,U,U,U,U,P,Z]
d.nf_live_palette_draw.argtypes=[C.c_uint64,U,U,U,U,P,P]
d.nf_live_completed_native_multimodel_pair_packet.argtypes=[P,P,C.c_double,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
d.nf_live_completed_native_multimodel_indexed_pair_packet.argtypes=d.nf_live_completed_native_multimodel_pair_packet.argtypes
world_indices='--world-indices' in sys.argv
d.nf_live_completed_native_multimodel_world_indexed_owned.argtypes=d.nf_live_completed_native_multimodel_owned.argtypes
indexed_endpoint=d.nf_live_completed_native_multimodel_world_indexed_owned if world_indices else d.nf_live_completed_native_multimodel_indexed_owned
indexed_pairs='--indexed-pairs' in sys.argv
pair_report=p/('native-indexed-multimodel-pair-tests.json' if indexed_pairs else 'native-multimodel-pair-tests.json')
pair_producer=d.nf_live_completed_native_multimodel_indexed_pair_packet if indexed_pairs else d.nf_live_completed_native_multimodel_pair_packet
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
published=0;multi=[];errors=[];first_packet=None;retained=[]
def section(packet,i):
 off,size=struct.unpack_from('<2I',packet,36+i*12);return packet[off:off+size]
@Sink
def sink(context,epoch,data,size):
 global published,first_packet
 try:
  packet=C.string_at(data,size);published+=1;models=section(packet,0);retained.append((epoch,packet));retained[:]=retained[-16:]
  if struct.unpack_from('<I',packet,4)[0]==2:
   magic,count=struct.unpack_from('<2I',models);assert magic==0x314c4d4e and 2<=count<=16
   identities=section(packet,4);worlds=struct.unpack_from('<I',section(packet,1),4)[0]
   ids=[];poses=[];hashes=[]
   for i in range(count):
    off,length=struct.unpack_from('<2I',models,8+i*8);asset=models[off:off+length];assert len(asset)==length and struct.unpack_from('<I',asset)[0]==0x324d464e
    row=struct.unpack_from('<5I',identities,8+20*(worlds+i));assert row[0]==3;ids.append(row[2]);poses.append(struct.unpack_from('<7d',asset,104));hashes.append(hashlib.sha256(asset).hexdigest())
   assert len(set(ids))==count and len(set(poses))==count
   multi.append(dict(serial=struct.unpack_from('<I',packet,16)[0],count=count,objects=ids,pose_hashes=hashes))
   if first_packet is None:first_packet=packet;(p/'live-first-multimodel.packet').write_bytes(packet)
  return 1
 except Exception as e:errors.append(repr(e));return 0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 blob=rom.read_bytes();assert d.nf_live_visibility_enable(blob,len(blob),16*1024*1024);d.nf_live_surface_audit_enable(1)
 for i in range(3583):d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 stats=(U*4)();d.nf_native_scene_stats(stats);assert not errors and stats[2]==0 and stats[3]==0 and multi,(errors,list(stats))
 world_endpoints=world_roads=world_index_bytes=0
 verified_inputs=0;atomic_guards=0;native_endpoints=0;native_model_bytes=0;palette_checks=[];indexed_models=0;indexed_texels=0
 for epoch,packet in retained:
  serial,begin,end,page=struct.unpack_from('<4I',packet,16);models=section(packet,0);identities=section(packet,4);worlds=struct.unpack_from('<I',section(packet,1),4)[0]
  count=U();assert d.nf_live_completed_models_count(epoch,serial,begin,end,C.byref(count))
  expected_count=struct.unpack_from('<I',models,4)[0] if struct.unpack_from('<I',packet,4)[0]==2 else 1;assert count.value==expected_count
  owned=P();owned_size=Z();stage=U()
  if not d.nf_live_completed_native_multimodel_owned(epoch,serial,begin,end,C.byref(owned),C.byref(owned_size),C.byref(stage)):
   (p/'native-multimodel-endpoint-tests.json').write_text(json.dumps(dict(result='FAIL',serial=serial,models=count.value,stage=stage.value,scope='Live native endpoint regeneration rejected; no gameplay pass'),indent=2));raise AssertionError(('native endpoint',serial,count.value,stage.value))
  try:generated=C.string_at(owned,owned_size.value)
  finally:d.nf_scene_packet_free(owned)
  generated_models=section(generated,0);generated_ids=section(generated,4);generated_worlds=struct.unpack_from('<I',section(generated,1),4)[0]
  indexed_owned=P();indexed_size=Z()
  assert indexed_endpoint(epoch,serial,begin,end,C.byref(indexed_owned),C.byref(indexed_size),C.byref(stage)),('indexed endpoint',serial,stage.value)
  try:
   indexed_packet=C.string_at(indexed_owned,indexed_size.value)
   if world_indices:
    indexed_world=section(indexed_packet,1);legacy_world=section(generated,1)
    assert indexed_world[:len(legacy_world)]==legacy_world,('world prefix changed',serial)
    pos=len(legacy_world);magic,world_count=struct.unpack_from('<2I',indexed_world,pos);assert magic==0x3149574e and world_count==worlds;pos+=8
    for wi in range(world_count):
     mode,n=struct.unpack_from('<2I',indexed_world,pos);pos+=8;kind=struct.unpack_from('<I',section(generated,4),8+wi*20)[0]
     assert mode==(1 if kind==1 else 0) and (n>0)==(kind==1),(serial,wi,kind,mode,n)
     world_roads+=int(mode==1);world_index_bytes+=n;pos+=n
    world_endpoints+=1
    assert pos==len(indexed_world)

  finally:d.nf_scene_packet_free(indexed_owned)
  indexed_section=section(indexed_packet,0);indexed_assets={}
  for j in range(count.value):
   off,length=struct.unpack_from('<2I',indexed_section,8+j*8) if count.value>1 else (0,len(indexed_section))
   indexed_assets[identities[8+(worlds+j)*20:28+(worlds+j)*20]]=indexed_section[off:off+length]
  generated_count=struct.unpack_from('<I',generated_models,4)[0] if struct.unpack_from('<I',generated,4)[0]==2 else 1;assert generated_count==count.value
  actual_models={}
  for j in range(generated_count):
   off,length=struct.unpack_from('<2I',generated_models,8+j*8) if generated_count>1 else (0,len(generated_models))
   actual_models[generated_ids[8+(generated_worlds+j)*20:28+(generated_worlds+j)*20]]=generated_models[off:off+length]
  for j in range(count.value):
   identity=identities[8+(worlds+j)*20:28+(worlds+j)*20];inputs=C.create_string_buffer(560)
   assert d.nf_live_completed_model_inputs_for(epoch,serial,begin,end,identity,inputs)
   indexed=indexed_assets[identity];original=actual_models[identity];width,height=struct.unpack_from('<2I',original,16);texels=width*height
   assert indexed[:len(original)]==original and struct.unpack_from('<4I',indexed,len(original))==(0x31495a4e,width,height,0)
   texture_indices=indexed[len(original)+16:];assert len(texture_indices)==texels
   palette_words=struct.unpack('<256H',inputs.raw[48:]);recolored=bytearray()
   for index in texture_indices:
    color=palette_words[index];recolored.extend(((color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31,255))
   assert bytes(recolored)==original[-texels*4:],('original indexed colors',serial,j)
   indexed_models+=1;indexed_texels+=texels
   scene_palette=C.create_string_buffer(512)
   scene_available=bool(d.nf_live_completed_snapshot_read(epoch,serial,begin,end,0x05000000,scene_palette,512))
   world_palettes={};world_colors={}
   for draw in range(256):
    key=(U*3)();candidate=C.create_string_buffer(512)
    if not d.nf_live_palette_draw(epoch,serial,begin,end,draw,key,candidate):break
    digest=hashlib.sha256(candidate.raw).hexdigest()
    world_colors[digest]=candidate.raw
    world_palettes.setdefault(digest,[]).append(list(key))
   width,height=struct.unpack_from('<2I',actual_models[identity],16);rgba=actual_models[identity][-width*height*4:]
   draw_hash=hashlib.sha256(inputs.raw[48:]).hexdigest()
   used_nonzero=set(texture_indices)-{0}
   assert world_colors and all(all(colors[index*2:index*2+2]==inputs.raw[48+index*2:50+index*2] for index in used_nonzero) for colors in world_colors.values()),('model nonzero palette provenance',serial,j)
   differences={digest:[index for index in range(256) if colors[index*2:index*2+2]!=inputs.raw[48+index*2:50+index*2]] for digest,colors in world_colors.items()}
   nearest=min(differences,key=lambda digest:len(differences[digest])) if differences else None
   palette_checks.append(dict(serial=serial,object=struct.unpack_from('<I',identity,8)[0],scene_palette_available=scene_available,full_palette_equal=scene_available and scene_palette.raw==inputs.raw[48:],draw_hash=draw_hash,scene_hash=hashlib.sha256(scene_palette.raw).hexdigest() if scene_available else None,world_palette_variants=len(world_palettes),world_palette_match_keys=world_palettes.get(draw_hash,[]),model_texture_hash=hashlib.sha256(rgba).hexdigest()))
   palette_checks[-1].update(nearest_world_palette=nearest,nearest_differing_indices=differences.get(nearest,[]),used_nonzero_colors=len(used_nonzero),all_world_banks_used_nonzero_match=True)
   identity_words=struct.unpack('<5I',identity);recovered=C.create_string_buffer(48)
   assert d.nf_live_completed_object_world_rotation(epoch,serial,begin,end,identity_words[1],identity_words[2],recovered)
   if recovered.raw[:36]!=inputs.raw[:36]:
    (p/'live-model-rotation-recovery-tests.json').write_text(json.dumps(dict(result='FAIL',serial=serial,object=identity_words[2],captured_matrix=list(struct.unpack('<12i',inputs.raw[:48])),recovered_matrix=list(struct.unpack('<12i',recovered.raw)),orientation_equal=recovered.raw[:36]==inputs.raw[:36],scope='Owned render-root rotation versus original draw rotation; no fallback verified'),indent=2))
    raise AssertionError(('recovered rotation mismatch',serial,j))
   off,length=struct.unpack_from('<2I',models,8+j*8) if count.value>1 else (0,len(models));asset=models[off:off+length]
   assert actual_models[identity]==asset,('native model mismatch',serial,j)
   native_model_bytes+=len(asset)
   origin=(C.c_double*3)();pose=(C.c_double*7)();assert d.nf_pose_decode(inputs,origin,pose)
   expected_quaternion=struct.unpack_from('<4d',asset,128);assert tuple(pose)[3:]==expected_quaternion
   verified_inputs+=1
   for wrong_epoch,wrong_serial,wrong_begin,wrong_end,bad_id in [(epoch+1,serial,begin,end,identity),(epoch,serial+1,begin,end,identity),(epoch,serial,begin+1,end,identity),(epoch,serial,begin,end+1,identity),(epoch,serial,begin,end,bytes(20))]:
    C.memset(inputs,0xA5,560);assert not d.nf_live_completed_model_inputs_for(wrong_epoch,wrong_serial,wrong_begin,wrong_end,bad_id,inputs);assert inputs.raw==bytes([0xA5])*560;atomic_guards+=1
  native_endpoints+=1
  if count.value>1:(p/'live-native-multimodel-endpoint.packet').write_bytes(generated)
  if count.value>1:(p/'live-native-indexed-endpoint.packet').write_bytes(indexed_packet)
 assert not d.nf_native_scene_multimodel(0)
 (p/'live-indexed-model-endpoint-tests.json').write_text(json.dumps(dict(result='PASS',scenes=native_endpoints,models=indexed_models,original_texels_verified=indexed_texels,scope='Native indexed endpoints: geometry/RGBA prefix exact to original captured model and retained indices with exact per-car draw palettes reproduce every texture texel; live display composition not yet integrated.'),indent=2))
 (p/'model-scene-palette-audit.json').write_text(json.dumps(dict(result='AUDIT',models=len(palette_checks),scene_palette_available=sum(row['scene_palette_available'] for row in palette_checks),full_palette_matches=sum(row['full_palette_equal'] for row in palette_checks),world_palette_matches=sum(bool(row['world_palette_match_keys']) for row in palette_checks),cases=palette_checks,scope='Exact retained scene/world draw palette provenance compared against per-car draw palettes; unavailable generic palettes are recorded, no fallback enabled.'),indent=2))
 (p/'live-model-rotation-recovery-tests.json').write_text(json.dumps(dict(result='PASS',owned_visible_orientations_exact=verified_inputs,scope='Nine Q14 orientation words exact against captured draw inputs; original translation scratch is unused by pose decode, which takes position from object record.'),indent=2))
 pair_checks=0;pair_models=0;pair_failed=False
 def model_map(packet):
  models=section(packet,0);identities=section(packet,4);worlds=struct.unpack_from('<I',section(packet,1),4)[0];count=struct.unpack_from('<I',models,4)[0] if struct.unpack_from('<I',packet,4)[0]==2 else 1;result={}
  for j in range(count):
   off,length=struct.unpack_from('<2I',models,8+j*8) if count>1 else (0,len(models));result[identities[8+(worlds+j)*20:28+(worlds+j)*20]]=models[off:off+length]
  return result
 for (epoch,a),(epoch_b,b) in zip(retained,retained[1:]):
  ids=[C.create_string_buffer(struct.pack('<Q5I',ep,*struct.unpack_from('<3I',packet,16),0,0),32) for ep,packet in [(epoch,a),(epoch_b,b)]]
  maps=[model_map(a),model_map(b)]
  for alpha in [0.25,0.5,0.75]:
   owned=P();owned_size=Z();stage=U()
   if not pair_producer(ids[0],ids[1],alpha,C.byref(owned),C.byref(owned_size),C.byref(stage)):
    missing=(U*6)();d.nf_live_paired_model_inputs_missing(missing)
    pair_report.write_text(json.dumps(dict(result='FAIL',indexed=indexed_pairs,serial=struct.unpack_from('<I',a,16)[0],alpha=alpha,stage=stage.value,successful_samples=pair_checks,verified_model_positions=pair_models,missing_endpoint_and_identity=list(missing),older_objects=[struct.unpack_from('<5I',identity)[2] for identity in maps[0]],newer_objects=[struct.unpack_from('<5I',identity)[2] for identity in maps[1]],scope='Multi-car native pair regeneration failure; no gameplay pass'),indent=2));pair_failed=True;break
   try:sampled_packet=C.string_at(owned,owned_size.value)
   finally:d.nf_scene_packet_free(owned)
   for identity,asset in model_map(sampled_packet).items():
    assert indexed_pairs or identity in maps[0]
    if indexed_pairs:
     width,height=struct.unpack_from('<2I',asset,16);base=160+struct.unpack_from('<I',asset,4)[0]*24+struct.unpack_from('<I',asset,8)[0]+struct.unpack_from('<I',asset,12)[0]*18+width*height*4
     assert struct.unpack_from('<4I',asset,base)==(0x31495a4e,width,height,0) and len(asset)==base+16+width*height
    positions=[]
    for ep,source,m in [(epoch,a,maps[0]),(epoch_b,b,maps[1])]:
     if identity in m:positions.append(struct.unpack_from('<3d',m[identity],104))
     else:
      record=C.create_string_buffer(164);serial,begin,end=struct.unpack_from('<3I',source,16);object_address=struct.unpack_from('<I',identity,8)[0]
      assert d.nf_live_completed_render_read(ep,serial,begin,end,object_address,record,164)
      positions.append(tuple(v/256 for v in struct.unpack_from('<3i',record.raw,12)))
    actual_position=struct.unpack_from('<3d',asset,104)
    for x,y,z in zip(*positions,actual_position):assert abs(z-(x+(y-x)*alpha))<=1/256
    pair_models+=1
   pair_checks+=1
  if pair_failed:break
 if not pair_failed:pair_report.write_text(json.dumps(dict(result='PASS',indexed=indexed_pairs,pairs_sampled=pair_checks,model_positions_verified=pair_models,scope='Retained live native multi-car scene regeneration at25/50/75percent; per-object positions Q8 verified, indexed metadata required for indexed mode. Live host integration and full route transition coverage pending.'),indent=2))
 actual={}
 for name,address,length in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'live-multimodel-{name}.bin';d.nf_dump(str(path).encode(),address,length);actual[name]=path.read_bytes()
finally:d.nf_close()
baseline=C.CDLL(str(p.parent/'nfsprobe.dll'));baseline.nf_init.argtypes=[C.c_char_p]*2;baseline.nf_state.argtypes=[C.c_char_p,C.c_int];baseline.nf_dump.argtypes=[C.c_char_p,U,U]
assert baseline.nf_init(str(rom).encode(),b'') and baseline.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for i in range(3583):baseline.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 for name,address,length in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'live-multimodel-baseline-{name}.bin';baseline.nf_dump(str(path).encode(),address,length);assert path.read_bytes()==actual[name],name
finally:baseline.nf_close()
report=dict(result='PASS',original_refreshes=3583,published=published,scene_stats=list(stats),multi_model_scenes=len(multi),first_multi_model=multi[0],max_models=max(row['count'] for row in multi),retained_per_object_inputs_verified=verified_inputs,atomic_identity_rejections=atomic_guards,ram_hashes={k:hashlib.sha256(v).hexdigest() for k,v in actual.items()},scope='Live opt-in complete snapshots and retained per-object rotations/palettes, quaternion equality to published assets; full route game RAM parity. Paired native generation and playable multi-car integration remain pending.')
(p/'live-multimodel-capture-tests.json').write_text(json.dumps(report,indent=2));print(report)
(p/'native-multimodel-endpoint-tests.json').write_text(json.dumps(dict(result='PASS',native_endpoints=native_endpoints,models=verified_inputs,model_bytes_exact=native_model_bytes,scope='Completed live native endpoint generation; every regenerated model exactly matches owned original-draw snapshot. Paired interpolation and playable integration pending.'),indent=2))
if pair_failed:raise AssertionError('Multi-car pair failure retained; endpoint/capture/final RAM checks completed independently')


if world_indices:
 world_report=dict(result='PASS',native_world_indexed_endpoints=world_endpoints,road_assets=world_roads,owned_road_index_bytes=world_index_bytes,world_geometry_rgba_prefix_exact=True,original_refreshes=3583,scope='Real retained endpoint world+model producer; all road metadata present and legacy world prefix exact, full original RAM parity. Paired road regeneration/GPU live integration not tested.')
 (p/'native-world-indexed-endpoint-tests.json').write_text(json.dumps(world_report,indent=2));print(world_report)
