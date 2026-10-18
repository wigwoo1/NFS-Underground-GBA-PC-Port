"""Regenerate complete captured NFB2 scenes and retain fractional visibility fixtures."""
import ctypes as C,csv,hashlib,json,struct,collections,sys
from pathlib import Path
camera=Path('work/camera').resolve();out=Path('outputs/nfsug-native-renderer/camera-research').resolve()
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=camera.parent/'driving.state';hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)]
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for value in (b'NF_LIVE_ROAD_ATTRIBUTES=1',b'NF_TRACE_NATIVE_COMMANDS=1'):assert crt._putenv(value)==0
d=C.CDLL(str(camera/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
class Identity(C.Structure):_fields_=[('epoch',C.c_uint64),('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('query',C.c_uint),('builder',C.c_uint)]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);retained=[]
@Sink
def sink(ctx,epoch,ptr,size):
 h=struct.unpack('<8I',C.string_at(ptr,32));retained.append((epoch,h[4],h[5],h[6]));retained[:]=retained[-16:];return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
pair=d.nf_live_completed_native_multimodel_world_classified_pair_packet;pair.argtypes=[C.POINTER(Identity),C.POINTER(Identity),C.c_double,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
trace=d.nf_visibility_snapshot_command_trace;trace.argtypes=[C.c_void_p,C.c_size_t];trace.restype=C.c_size_t
fixture=d.nf_visibility_snapshot_query_fixture;fixture.argtypes=[C.c_void_p,C.c_size_t];fixture.restype=C.c_size_t
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));assert session['status']=='HOST_COMPLETE' and session['live_model_bounds'] and session['live_road_attributes']
assert hashes==[session[name+'_sha256'].lower() for name in ('rom','state')]
dense='--dense' in sys.argv
prefix=Path(session['prefix']);files=sorted(prefix.parent.glob(prefix.name+('-dense-' if dense else '-capture-')+'*-native-source.json'));assert len(files)==(session['dense_frames'] if dense else 12)
samples=[]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 blob=C.create_string_buffer(rom.read_bytes());assert d.nf_live_visibility_enable(blob,len(blob)-1,16*1024*1024);d.nf_live_surface_audit_enable(1)
 wanted={end for file in files for end in json.loads(file.read_text())['source_refreshes']};replay_updates=0
 for i,row in enumerate(csv.DictReader(Path(str(prefix)+'-input.csv').open())):
  assert int(row['index'])==i;d.nf_frame(int(row['keys']));replay_updates+=1
  if wanted<={identity[3] for identity in retained}:break
 assert wanted<={identity[3] for identity in retained},'Recorded inputs ended before required original endpoints'
 for file in files:
  meta=json.loads(file.read_text());captured=Path(str(file).replace('-native-source.json','-native-scene.bin')).read_bytes()
  ids_offset=struct.unpack_from('<I',captured,84)[0];ids_count=struct.unpack_from('<I',captured,ids_offset+4)[0];exact_alpha=struct.unpack_from('<d',captured,ids_offset+8+ids_count*20+8)[0];alpha=exact_alpha
  ids=[Identity(*next(identity for identity in retained if identity[3]==end),0,0) for end in meta['source_refreshes']]
  ptr=C.c_void_p();size=C.c_size_t();stage=C.c_uint();assert pair(C.byref(ids[0]),C.byref(ids[1]),alpha,C.byref(ptr),C.byref(size),C.byref(stage)),stage.value
  try:packet=C.string_at(ptr,size.value)
  finally:d.nf_scene_packet_free(ptr)
  assert packet==captured,('independent scene regeneration mismatch',str(file))
  buf=C.create_string_buffer(20000);n=trace(buf,len(buf));assert n;raw=buf.raw[:n];count,roots=struct.unpack_from('<2I',raw);assert n==(2+roots*4+count*16)*4
  source=C.create_string_buffer(120+0x48000);assert fixture(source,len(source))==len(source);fixture_path=Path(str(file).replace('-native-source.json','-query-fixture.bin'));fixture_path.write_bytes(source.raw)
  queue=[struct.unpack_from('<8H',raw,8+i*16) for i in range(roots)];commands=[]
  for i in range(count):
   row=struct.unpack_from('<16I',raw,8+roots*16+i*64);record=struct.unpack('<8H',struct.pack('<4I',*row[10:14]));commands.append(dict(index=i,kind=row[0],owner=row[1],pass_number=row[2],mask=row[3],object=row[4],source=hex(row[5]),bounds=row[6:10],record=record,viewport=row[14:16]))
  counter=collections.Counter((c['kind'],c['source']) for c in commands if c['kind'] in (1,2));duplicates=[dict(kind=k[0],source=k[1],commands=[c for c in commands if (c['kind'],c['source'])==k]) for k,n in counter.items() if n>1]
  samples.append(dict(target=meta['target'],source_refreshes=meta['source_refreshes'],alpha=alpha,query_fixture=str(fixture_path),queue=queue,commands=commands,repeated_world_sources=duplicates,packet_sha256=hashlib.sha256(packet).hexdigest(),affected_capture_exact=(packet==captured) if alpha==exact_alpha else None))
finally:d.nf_close()
assert hashes==[hashlib.sha256(p.read_bytes()).hexdigest() for p in (rom,state)]
report=dict(result='TRACED',manifest=str(manifest),input_ledger_sha256=hashlib.sha256(Path(str(prefix)+'-input.csv').read_bytes()).hexdigest(),original_updates=replay_updates,samples=samples,scope='Every configured captured live NFB2 scene regenerates byte exactly from independently replayed recorded original inputs with live road attributes. Exact double alpha retained, complete query fixtures and command portals exported. Original ARM traversal and raster fidelity are separate verifications.')
Path(str(prefix)+('-dense' if dense else '')+'-fractional-command-trace.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='TRACED',samples=[dict(alpha=s['alpha'],queue_regions=[q[0] for q in s['queue']],repeated_sources=[c['source'] for c in s['repeated_world_sources']]) for s in samples]),indent=2))
