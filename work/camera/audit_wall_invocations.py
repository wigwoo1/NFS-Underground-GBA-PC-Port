from pathlib import Path
import ctypes as C,csv,json,struct,hashlib,os
os.environ["NF_LIVE_ROAD_ATTRIBUTES"]="1"
# MinGW bridge uses msvcrt getenv; update its CRT environment explicitly.
crt=C.CDLL("msvcrt");crt._putenv.argtypes=[C.c_char_p];assert crt._putenv(b"NF_LIVE_ROAD_ATTRIBUTES=1")==0
p=Path('work/camera').resolve();out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';prefix=p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13'
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);scenes=[]
@Sink
def receive(ctx,epoch,ptr,size):
 h=struct.unpack_from('<8I',C.string_at(ptr,32));scenes.append((epoch,h[4],h[5],h[6]));return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
records=[];poses=[];projections=[];regions=[];dispatch=[]
try:
 assert d.nf_native_scene_sink(receive,None) and d.nf_native_scene_multimodel(1)
 data=rom.read_bytes();buf=C.create_string_buffer(data);assert d.nf_live_visibility_enable(buf,len(data),16*1024*1024);d.nf_live_surface_audit_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']))
  if int(row['after'])>=8926:break
 identity=next(x for x in scenes if x[1:]==(9,8877,8881))
 d.nf_live_completed_visibility_pose.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
 for item in (identity,next(x for x in scenes if x[1:]==(10,8881,8885))):
  pose=(C.c_uint*26)();assert d.nf_live_completed_visibility_pose(*item,pose);poses.append(dict(scene=item,base=list(pose)[:2],query=list(pose)[2:14],view=list(pose)[14:26]))
  for snapshot in ('snapshot','render'):
   read=getattr(d,'nf_live_completed_'+snapshot+'_read');read.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t]
   pointer=(C.c_uint*1)();assert read(*item,0x030000c0+80,pointer,4)
   raw=(C.c_ubyte*32)();assert read(*item,pointer[0],raw,32)
   data=bytes(raw);projections.append(dict(scene=item,snapshot=snapshot,address=pointer[0],raw_hex=data.hex(),center=list(struct.unpack_from('<2h',data,8)),near=struct.unpack_from('<i',data,16)[0],scale=struct.unpack_from('<i',data,28)[0]))
 d.nf_visibility_pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p]
 endpoints=[(C.c_uint*26)(*(r['base']+r['query']+r['view'])) for r in poses]
 sampled=(C.c_uint*26)();alpha=json.loads(Path(str(prefix)+'-native-source.json').read_text())['alpha']
 assert d.nf_visibility_pose_sample(endpoints[0],endpoints[1],alpha,sampled)
 d.nf_live_completed_region_at.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
 read=d.nf_live_completed_snapshot_read
 for label,pose in [('older',endpoints[0]),('sampled',sampled)]:
  for ordinal in range(64):
   raw=(C.c_ubyte*(256+16+32*52+64*24))()
   if not d.nf_live_completed_region_at(*identity,pose,ordinal,raw):continue
   data=bytes(raw);region_index=struct.unpack_from('<H',data,256)[0];table=struct.unpack_from('<I',data,20)[0];base=struct.unpack_from('<I',data,16)[0]
   descriptor=(C.c_ubyte*48)();assert read(*identity,table+region_index*48,descriptor,48)
   first,count=struct.unpack_from('<HH',bytes(descriptor));assert count<=32
   edges=[]
   for edge in range(count):
    source=base+(first+edge)*68
    if source not in (0x085747fc,0x08574840,0x08574884,0x085748c8,0x0857c6f4):continue
    scratch=data[272+edge*52:272+(edge+1)*52]
    edges.append(dict(source=hex(source),scratch_hex=scratch.hex(),projected_xy_depth=list(struct.unpack_from('<8h',scratch)),flags=struct.unpack_from('<H',scratch,48)[0]))
   if edges:regions.append(dict(pose=label,queue_ordinal=ordinal,region_index=region_index,edges=edges))
 for name in ['surface_identity','surface_arguments','surface_origin','surface_bounds','wall_pass','wall_animation']:
  getattr(d,'nf_live_completed_'+name).argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
 for ordinal in range(256):
  ids=(C.c_uint*5)()
  if not d.nf_live_completed_surface_identity(*identity,ordinal,ids):break
  record=dict(ordinal=ordinal,identity=list(ids))
  for name,size,typ in [('surface_arguments',12,C.c_uint),('surface_origin',12,C.c_uint),('surface_bounds',4,C.c_ushort),('wall_pass',3,C.c_uint),('wall_animation',12,C.c_uint)]:
   result=(typ*size)()
   if getattr(d,'nf_live_completed_'+name)(*identity,ordinal,result):record[name]=list(result)
  records.append(record)
 d.nf_live_completed_dispatch.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
 commands=(C.c_uint*(257*6))();command_count=C.c_uint()
 assert d.nf_live_completed_dispatch(*identity,commands,257,C.byref(command_count))
 dispatch=[list(commands)[i*6:(i+1)*6] for i in range(command_count.value)]
 # Object-selected chevron is outside the visibility queue. Reconstruct its
 # retained record with the same pose-overlay reader used by the C adapter.
 d.nf_live_completed_object_region.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
 Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t)
 d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
 target=next(r for r in records if r['identity'][2]==0x0857c6f4)
 owned=(C.c_ubyte*184)();assert d.nf_live_completed_object_region(*identity,target['ordinal'],owned)
 region_record=bytes(owned)[168:184];region_index=struct.unpack_from('<H',region_record)[0]
 original_state=(C.c_ubyte*256)();assert d.nf_live_completed_render_read(*identity,target['identity'][1],original_state,256)
 matrix_address=struct.unpack_from('<I',bytes(original_state),84)[0]
 reciprocal=(C.c_uint*32768).from_buffer_copy(rom.read_bytes()[0x627700:0x627700+32768*4])
 for label,pose in [('older',endpoints[0]),('sampled',sampled)]:
  view=bytes(pose)[56:104]
  @Read
  def pose_read(ctx,address,output,size):
   if not read(*identity,address,output,size):return 0
   lo=max(address,matrix_address);hi=min(address+size,matrix_address+48)
   if lo<hi:C.memmove(output+lo-address,view[lo-matrix_address:hi-matrix_address],hi-lo)
   return 1
  st=(C.c_ubyte*256).from_buffer_copy(bytes(original_state));record_buffer=C.create_string_buffer(region_record)
  scratch=(C.c_ubyte*(32*52))();stream=(C.c_ubyte*(64*24))()
  assert d.nfs_visibility_region_reconstruct(st,record_buffer,pose_read,None,reciprocal,scratch,len(scratch),stream,len(stream))==1
  table=struct.unpack_from('<I',bytes(st),20)[0];base=struct.unpack_from('<I',bytes(st),16)[0]
  descriptor=(C.c_ubyte*48)();assert read(*identity,table+region_index*48,descriptor,48)
  first,count=struct.unpack_from('<HH',bytes(descriptor));assert count<=32
  edges=[]
  for edge in range(count):
   source=base+(first+edge)*68
   if source!=0x0857c6f4:continue
   raw=bytes(scratch)[edge*52:(edge+1)*52]
   edges.append(dict(source=hex(source),scratch_hex=raw.hex(),projected_xy_depth=list(struct.unpack_from('<8h',raw)),flags=struct.unpack_from('<H',raw,48)[0]))
  assert len(edges)==1
  regions.append(dict(pose=label,object_address=struct.unpack_from('<I',bytes(owned))[0],surface_ordinal=target['ordinal'],region_index=region_index,edges=edges))
 d.nf_live_completed_native_multimodel_world_classified_owned.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
 d.nf_scene_packet_free.argtypes=[C.c_void_p]
 exports=[]
 for export_identity in [x for x in scenes if 9<=x[1]<=20]:
  endpoint_packet=C.c_void_p();endpoint_size=C.c_size_t();endpoint_stage=C.c_uint()
  assert d.nf_live_completed_native_multimodel_world_classified_owned(*export_identity,C.byref(endpoint_packet),C.byref(endpoint_size),C.byref(endpoint_stage)), endpoint_stage.value
  try:
   raw=C.string_at(endpoint_packet,endpoint_size.value);path=p/f'scene{export_identity[1]}-original-pose.packet';path.write_bytes(raw)
   exports.append(dict(identity=export_identity,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(path)))
  finally:d.nf_scene_packet_free(endpoint_packet)
 road_identity=next(x for x in scenes if x[1:]==(10,8881,8885));road_records=[]
 for ordinal in range(256):
  ids=(C.c_uint*5)()
  if not d.nf_live_completed_surface_identity(*road_identity,ordinal,ids):break
  if ids[2]!=0x0856b5d0:continue
  arguments=(C.c_uint*12)();bounds=(C.c_ushort*4)();assert d.nf_live_completed_surface_arguments(*road_identity,ordinal,arguments);assert d.nf_live_completed_surface_bounds(*road_identity,ordinal,bounds)
  reads={}
  for label,address,size in [('state',ids[1],256),('descriptor',ids[2],48)]:
   raw=(C.c_ubyte*size)();assert d.nf_live_completed_render_read(*road_identity,address,raw,size),(label,hex(address),list(ids));reads[label]=bytes(raw).hex()
  state_raw=bytes.fromhex(reads['state']);descriptor_raw=bytes.fromhex(reads['descriptor'])
  table=struct.unpack_from('<I',state_raw,32)[0];material_index=struct.unpack_from('<H',descriptor_raw,8)[0]
  initial=(C.c_ubyte*32)();assert d.nf_live_completed_render_read(*road_identity,table+material_index*32,initial,32)
  animation_address=struct.unpack_from('<I',state_raw,72)[0]+struct.unpack_from('<H',bytes(initial))[0]*8
  animation=(C.c_ubyte*8)();assert d.nf_live_completed_render_read(*road_identity,animation_address,animation,8)
  material_address=table+(material_index+struct.unpack_from('<H',bytes(animation),2)[0])*32
  material=(C.c_ubyte*32)();assert d.nf_live_completed_render_read(*road_identity,material_address,material,32)
  reads.update(material=bytes(material).hex(),animation=bytes(animation).hex(),material_address=material_address,animation_address=animation_address)
  road_records.append(dict(ordinal=ordinal,identity=list(ids),arguments=list(arguments),bounds=list(bounds),reads=reads))
 assert len(road_records)==1
 (out/'scene10-road5-original-invocation.json').write_text(json.dumps(road_records,indent=2))
 (out/'original-pose-endpoint-exports.json').write_text(json.dumps(dict(exports=exports,road_attributes_requested=True,scope='Adjacent retained complete-scene original-pose exports; no interpolated motion proof'),indent=2))

finally:d.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
sources={0x085747fc,0x08574840,0x08574884,0x085748c8,0x0857c6f4}
selected=[r for r in records if r['identity'][2] in sources]
report=dict(result='CAPTURED',scene=identity,visibility_poses=poses,world_projections=projections,suspect_regions=regions,original_dispatch=dispatch,total_original_draws=len(records),suspect_draws=selected,all_draws=records,rom_state_unchanged=True,scope='Retained invocation-time surface records from exact original replay scene. Candidate native surfaces can exist without an original draw; absence alone does not prove invalid sampled visibility.')
(out/'native-wall-invocation-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(total=len(records),suspect_regions=regions),indent=2))
