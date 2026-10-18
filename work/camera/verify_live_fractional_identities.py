"""Verify live fractional model/world identities against original endpoint scenes."""
import ctypes as C,csv,hashlib,json,struct,collections,sys
from pathlib import Path
camera=Path('work/camera').resolve();out=Path('outputs/nfsug-native-renderer/camera-research').resolve()
manifest=Path(sys.argv[1]) if len(sys.argv)>1 else None
session=json.loads(manifest.read_text(encoding='utf-8-sig')) if manifest else None
prefix=Path(session['prefix']) if session else camera/'prototype-runs'/'threaded-route-20fd179dba974550a890b815a32ddf1c'
if session:assert session['status']=='HOST_COMPLETE' and (session.get('steering_route') or session.get('selection_route'))
dense='--dense' in sys.argv
files=sorted(prefix.parent.glob(prefix.name+('-dense-' if dense else '-capture-')+'*-native-source.json'))
assert len(files)==(session['dense_frames'] if dense else 12),'Expected complete configured capture sequence'
metas=[json.loads(f.read_text()) for f in files];wanted={e for m in metas for e in m['source_refreshes']}
object_requests={end:set() for end in wanted}
for file,meta in zip(files,metas):
 packet=Path(str(file).replace('-native-source.json','-native-scene.bin')).read_bytes();sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))};world=struct.unpack_from('<I',sections[2],4)[0];model_count=struct.unpack_from('<I',sections[1],4)[0] if sections[1][:4]==b'NML1' else 1
 for j in range(model_count):
  key=struct.unpack_from('<5I',sections[5],8+(world+j)*20)
  for end in meta['source_refreshes']:object_requests[end].add(key)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=Path(session['state']) if session else camera.parent/'driving.state';hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)]
if session:assert hashes==[session[name+'_sha256'].lower() for name in ('rom','state')]
d=C.CDLL(str(camera/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);retained=[]
@Sink
def sink(ctx,epoch,ptr,size):
 h=struct.unpack('<8I',C.string_at(ptr,32));retained.append((epoch,h[4],h[5],h[6]));retained[:]=retained[-16:];return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
d.nf_live_completed_native_multimodel_world_classified_owned.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];assert crt._putenv(b'NF_LIVE_ROAD_ATTRIBUTES=1')==0
if session and session.get('selection_route'):assert crt._putenv(b'NF_CAPTURE_MODEL_VIEWS=1')==0
original={};exports=[];object_pose_inputs=[];missing_object_pose_inputs=[]
d.nf_live_completed_object_pose_inputs.argtypes=[C.c_uint64]+[C.c_uint]*5+[C.c_void_p,C.c_void_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 blob=C.create_string_buffer(rom.read_bytes());assert d.nf_live_visibility_enable(blob,len(blob)-1,16*1024*1024);d.nf_live_surface_audit_enable(1)
 replay_updates=0
 inputs=list(csv.DictReader(Path(str(prefix)+'-input.csv').open())) if session else [dict(index=i,keys=1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0)) for i in range(3550)]
 for i,row in enumerate(inputs):
  assert int(row['index'])==i;d.nf_frame(int(row['keys']));replay_updates+=1
  if wanted<={identity[3] for identity in retained}:break
 assert wanted<={identity[3] for identity in retained},'Recorded inputs ended before required original endpoints'
 for identity in retained:
  if identity[3] not in wanted:continue
  ptr=C.c_void_p();size=C.c_size_t();stage=C.c_uint();assert d.nf_live_completed_native_multimodel_world_classified_owned(*identity,C.byref(ptr),C.byref(size),C.byref(stage))
  try:data=C.string_at(ptr,size.value)
  finally:d.nf_scene_packet_free(ptr)
  original[identity[3]]=data;path=Path(str(prefix)+f'-endpoint-{identity[1]}.packet') if dense else camera/f'visibility-original-{identity[1]}.packet';path.write_bytes(data);exports.append(dict(identity=identity,path=str(path),sha256=hashlib.sha256(data).hexdigest()))
  for key in sorted(object_requests[identity[3]]):
   record=C.create_string_buffer(164);matrix=(C.c_int32*12)();found=d.nf_live_completed_object_pose_inputs(*identity,key[1],key[2],record,matrix)
   if not found:
    assert session and session.get('selection_route'),'Missing required driving object pose'
    missing_object_pose_inputs.append(dict(endpoint_refresh=identity[3],identity=key));continue
   object_pose_inputs.append(dict(endpoint_refresh=identity[3],identity=key,record_hex=record.raw.hex(),record_sha256=hashlib.sha256(record.raw).hexdigest(),world_rotation=list(matrix)))
   # Invalid unaligned object identity must fail without publishing partial data.
   bad_record=C.create_string_buffer(b'R'*164,164);bad_matrix=C.create_string_buffer(b'M'*48,48)
   assert not d.nf_live_completed_object_pose_inputs(*identity,key[1],key[2]+1,bad_record,bad_matrix)
   assert bad_record.raw==b'R'*164 and bad_matrix.raw==b'M'*48
finally:d.nf_close()
assert wanted==original.keys(),f'Missing original endpoints: {wanted-original.keys()}'
def parse(data):
 sections={}
 for j in range(5):
  tag,offset,size=struct.unpack_from('<III',data,32+j*12);sections[tag]=data[offset:offset+size]
 world=struct.unpack_from('<I',sections[2],4)[0];m=sections[1];models=struct.unpack_from('<I',m,4)[0] if m[:4]==b'NML1' else 1
 ids=[struct.unpack_from('<5I',sections[5],8+20*i) for i in range(world+models)]
 count=struct.unpack_from('<I',sections[3],4)[0];commands=struct.unpack_from('<'+str(count)+'I',sections[3],8)
 assert len(set(commands))==count and set(commands)==set(range(world))|{0xffffffff-i for i in range(models)}
 assert len(set(ids[world:]))==models
 duplicates=[dict(identity=k,ordinals=[i for i,v in enumerate(ids[:world]) if v==k]) for k,n in collections.Counter(ids[:world]).items() if n>1]
 position=8;surfaces=[]
 for i in range(world):
  begin=position;n,width,height=struct.unpack_from('<3I',sections[2],position);position+=12+n*40+width*height*4;surfaces.append(sections[2][begin:position])
 trailer=8+(world+models)*20
 for duplicate in duplicates:
  ordinals=duplicate['ordinals'];duplicate['exact_surface_bytes']=all(surfaces[i]==surfaces[ordinals[0]] for i in ordinals)
  duplicate['sampled_bounds']=[struct.unpack_from('<4H',sections[5],trailer+16+8*i) for i in ordinals]
  duplicate['command_positions']=[commands.index(i) for i in ordinals]
 return dict(world=ids[:world],models=ids[world:],commands=commands,duplicate_world_identities=duplicates)
endpoints={e:parse(data) for e,data in original.items()};checks=[]
for file,meta in zip(files,metas):
 native=parse(Path(str(file).replace('-native-source.json','-native-scene.bin')).read_bytes());left,right=[endpoints[e] for e in meta['source_refreshes']]
 for kind in ('models','world'):assert set(native[kind])<=set(left[kind])|set(right[kind]),f'Unexpected {kind} source at {meta["target"]}'
 checks.append(dict(target=meta['target'],alpha=meta['alpha'],source_refreshes=meta['source_refreshes'],endpoint_model_counts=[len(left['models']),len(right['models'])],native_model_count=len(native['models']),model_identities=native['models'],world_count=len(native['world']),endpoint_world_counts=[len(left['world']),len(right['world'])],duplicate_world_identities=native['duplicate_world_identities'],all_source_identities_known=True,each_command_exactly_once=True))
assert hashes==[hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)]
report=dict(result='PASS',manifest=str(manifest) if manifest else None,input_ledger_sha256=hashlib.sha256(Path(str(prefix)+'-input.csv').read_bytes()).hexdigest() if session else None,original_updates=replay_updates,original_endpoints=exports,checks=checks,scope='Every live model/world identity belongs to its original endpoint union regenerated from recorded original inputs; each command appears exactly once. Model identities are unique. Repeated world sources are reported and preserved; original ARM parity is a separate test. Does not prove interpolated traversal coverage, occlusion or visibility cutoff correctness.')
report['missing_original_object_pose_inputs']=missing_object_pose_inputs
report['original_object_pose_inputs']=object_pose_inputs
report['invalid_pose_export_atomic_checks']=len(object_pose_inputs)
report_path=Path(str(prefix)+('-dense' if dense else '')+'-source-identity-verification.json') if manifest else out/'live-fractional-source-identity-verification.json'
report_path.write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',frames=len(checks),original_endpoints=len(exports),frames_with_repeated_world_sources=sum(bool(c['duplicate_world_identities']) for c in checks),model_counts=[c['native_model_count'] for c in checks])))
