"""Owned per-draw view retention across original RAM updates."""
import ctypes as C,json,struct,os,sys
from pathlib import Path
second_transition='--second-transition' in sys.argv
os.environ['NF_CAPTURE_MODEL_VIEWS']='1'
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
p=Path(__file__).resolve().parent;P=C.c_void_p;Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,C.c_size_t);d=C.CDLL(str(p/'visibility-probe-wide.dll'))
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,P];d.nf_live_visibility_enable.argtypes=[P,C.c_size_t,C.c_size_t];d.nf_live_completed_draw_view.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,P]
d.nf_live_completed_draw_root.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,P,P]
U=C.c_uint32
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
d.nf_live_completed_draw_builder_result.argtypes=[C.c_uint64,U,U,P]
d.nf_live_completed_draw_root_captured.argtypes=[C.c_uint64,U,U,P]
d.nf_live_completed_draw_root_commands.argtypes=[C.c_uint64,U,U,P,U,P]
d.nf_live_completed_draw_root_cameras.argtypes=[C.c_uint64,U,U,P,U,P]
source_order=[];source_assets=[];source_models=[];source_packets=[]
d.nf_live_completed_draw_model_indexed_asset.argtypes=[C.c_uint64,U,U,P,P]
d.nf_live_completed_draw_model_asset.argtypes=[C.c_uint64,U,U,P,P]
d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P]
d.nf_live_completed_draw_root_metadata.argtypes=[C.c_uint64,U,U,U,P,P,P]
d.nf_live_completed_draw_root_asset.argtypes=[C.c_uint64,U,U,U,P,P,P,P];d.nf_surface_free.argtypes=[P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');owned=[]
@Sink
def sink(ctx,epoch,data,size):
 raw=C.string_at(data,size);serial=struct.unpack_from('<I',raw,16)[0];off,n=struct.unpack_from('<2I',raw,36);section=raw[off:off+n]
 if section[:4]==b'NML1' and not owned and (not second_transition or serial==38):
  source_packets.append(raw)
  count=struct.unpack_from('<I',section,4)[0]
  for k in range(count):
   mo,ms=struct.unpack_from('<2I',section,8+k*8);source_models.append(section[mo:mo+ms])
  order_off,order_size=struct.unpack_from('<2I',raw,60);identity_off,identity_size=struct.unpack_from('<2I',raw,84);order=raw[order_off:order_off+order_size];identities=raw[identity_off:identity_off+identity_size]
  wo,ws=struct.unpack_from('<2I',raw,48);lo,ls=struct.unpack_from('<2I',raw,72);world=raw[wo:wo+ws];lighting=raw[lo:lo+ls];wp=lp=8;assets=[]
  for _ in range(struct.unpack_from('<I',world,4)[0]):
   corners,width,height=struct.unpack_from('<3I',world,wp);size=12+corners*40+width*height*4;lit=struct.unpack_from('<I',lighting,lp)[0];light_size=20+width*height*64 if lit else 4;assets.append((world[wp:wp+size],lighting[lp:lp+light_size]));wp+=size;lp+=light_size
  for k in range(struct.unpack_from('<I',order,4)[0]):
   value=struct.unpack_from('<I',order,8+k*4)[0];world_offset,world_size=struct.unpack_from('<2I',raw,48);world_count=struct.unpack_from('<I',raw,world_offset+4)[0];index=world_count+(0xffffffff-value) if value>=0xfffffff0 else value;identity=struct.unpack_from('<5I',identities,8+index*20);source_order.append((identity[0],identity[2],identity[3]));source_assets.append(None if identity[0]==3 else assets[value])
  for ordinal in range(count):
   view=C.create_string_buffer(48)
   if not d.nf_live_completed_draw_view(epoch,serial,ordinal,view):return 0
   owned.append((epoch,serial,ordinal,view.raw))
 return 1
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p/'prototype-runs/menu-navigation/quick-1-release.state').encode(),0)
assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1);raw=rom.read_bytes();assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);d.nf_live_surface_audit_enable(1)
try:
 for i in range(240):
  d.nf_frame(16 if 90<=i<92 or 180<=i<182 else 0)
  if owned:break
 assert len(owned)==2
 for _ in range(8):d.nf_frame(0)
 reconstructed_order=[];asset_checks=0
 if second_transition:
  captured_order=[];d.nf_live_completed_draw_root_captured_commands.argtypes=[C.c_uint64,U,U,P,U,P]
  for epoch,serial,ordinal,_ in owned:
   commands=(Command*144)();count=U();assert d.nf_live_completed_draw_root_captured_commands(epoch,serial,ordinal,commands,144,C.byref(count))
   for i in range(count.value):
    command=commands[i];kind=command.head[0];material=struct.unpack_from('<I',bytes(command.model),12)[0] if kind==5 else (4 if command.head[8] else 8) if kind==1 else (command.head[9]-struct.unpack_from('<I',bytes(command.state),32)[0])//32
    captured_order.append((3 if kind==5 else kind,command.head[5],material))
  print('captured_native_plan_order_exact',captured_order==source_order,'commands',len(captured_order),'original',len(source_order))
 for epoch,serial,ordinal,expected in owned:
  model=P();model_size=C.c_size_t();assert d.nf_live_completed_draw_model_asset(epoch,serial,ordinal,C.byref(model),C.byref(model_size))
  try:assert C.string_at(model,model_size.value)==source_models[ordinal]
  finally:d.nf_surface_free(model)
  tagged=P();tagged_size=C.c_size_t();assert d.nf_live_completed_draw_model_indexed_asset(epoch,serial,ordinal,C.byref(tagged),C.byref(tagged_size))
  try:
   tagged_bytes=C.string_at(tagged,tagged_size.value);original=source_models[ordinal];width,height=struct.unpack_from('<2I',original,16)
   assert tagged_bytes[:len(original)]==original and len(tagged_bytes)==len(original)+16+width*height
   assert struct.unpack_from('<4I',tagged_bytes,len(original))==(0x31495a4e,width,height,0)
  finally:d.nf_surface_free(tagged)
  view=C.create_string_buffer(48);assert d.nf_live_completed_draw_view(epoch,serial,ordinal,view) and view.raw==expected
  root_view=C.create_string_buffer(48);root_result=C.create_string_buffer(4868);assert d.nf_live_completed_draw_root(epoch,serial,ordinal,root_view,root_result) and root_view.raw==expected
  captured=C.create_string_buffer(4868);assert d.nf_live_completed_draw_root_captured(epoch,serial,ordinal,captured)
  if second_transition:
   builder=C.create_string_buffer(4868);assert d.nf_live_completed_draw_builder_result(epoch,serial,ordinal,builder)
   print('entry_builder_matches_root_queue_groups',ordinal,builder.raw[256:4864]==captured.raw[256:4864])
   print('builder_comparison',ordinal,[(k,a,b) for k,(a,b) in enumerate(zip(root_result.raw[:4864],captured.raw[:4864])) if a!=b][:24])
  commands=(Command*144)();count=U();assert d.nf_live_completed_draw_root_commands(epoch,serial,ordinal,commands,144,C.byref(count))
  cameras=C.create_string_buffer(144*56);camera_count=U();assert d.nf_live_completed_draw_root_cameras(epoch,serial,ordinal,cameras,144,C.byref(camera_count)) and camera_count.value==count.value
  assert all(cameras.raw[k*56:(k+1)*56]==source_models[ordinal][48:104] for k in range(count.value))
  for i in range(count.value):
   command=commands[i];kind=command.head[0];material=struct.unpack_from('<I',bytes(command.model),12)[0] if kind==5 else (4 if command.head[8] else 8) if kind==1 else (command.head[9]-struct.unpack_from('<I',bytes(command.state),32)[0])//32
   if kind in [1,2]:
    asset=P();size=C.c_size_t();light=P();light_size=C.c_size_t();detail=(U*7)();ok=d.nf_live_completed_draw_root_asset(epoch,serial,ordinal,i,C.byref(asset),C.byref(size),C.byref(light),C.byref(light_size));d.nf_live_draw_root_asset_detail(detail);assert ok,dict(ordinal=ordinal,index=i,detail=list(detail),native_command=(kind,command.head[5],material),original_command=source_order[len(reconstructed_order)])
    try:
     actual=(C.string_at(asset,size.value),C.string_at(light,light_size.value) if light_size.value else struct.pack('<I',0));expected_asset=source_assets[len(reconstructed_order)]
     differences=[dict(section=j,actual_size=len(a),expected_size=len(b),first_difference=next((k for k,(x,y) in enumerate(zip(a,b)) if x!=y),None)) for j,(a,b) in enumerate(zip(actual,expected_asset)) if a!=b]
     assert not differences,dict(ordinal=ordinal,index=i,kind=kind,source=command.head[5],differences=differences)
    finally:d.nf_surface_free(asset);d.nf_surface_free(light)
    metadata=P();metadata_size=C.c_size_t();metadata_mode=U();assert d.nf_live_completed_draw_root_metadata(epoch,serial,ordinal,i,C.byref(metadata),C.byref(metadata_size),C.byref(metadata_mode))
    try:
     corners,width,height=struct.unpack_from('<3I',actual[0]);payload=C.string_at(metadata,metadata_size.value)
     if kind==1:
      assert metadata_mode.value in [5,6] and len(payload)==width*height+288
      assert struct.unpack_from('<I',payload,width*height)[0]==corners
     else:
      assert metadata_mode.value in [2,3] and len(payload)==width*height*(17 if metadata_mode.value==3 else 1)
      assert set(payload)<=set([0,1,2]) and 1 not in payload[:width*height]
    finally:d.nf_surface_free(metadata)
    asset_checks+=1
   reconstructed_order.append((3 if kind==5 else kind,command.head[5],material))
  for wrong_epoch,wrong_ordinal in [(epoch+1,ordinal),(epoch,4)]:
   sentinel_asset=P(165);sentinel_size=C.c_size_t(165);assert not d.nf_live_completed_draw_model_asset(wrong_epoch,serial,wrong_ordinal,C.byref(sentinel_asset),C.byref(sentinel_size)) and sentinel_asset.value==165 and sentinel_size.value==165
   sentinel=C.create_string_buffer(bytes([165])*48,48);assert not d.nf_live_completed_draw_view(wrong_epoch,serial,wrong_ordinal,sentinel) and sentinel.raw==bytes([165])*48
 assert reconstructed_order==source_order,(reconstructed_order,source_order)
 packet=P();packet_size=C.c_size_t();scene_cameras=C.create_string_buffer(144*56);scene_count=U()
 assert d.nf_live_completed_draw_scene_packet(owned[0][0],owned[0][1],C.byref(packet),C.byref(packet_size),scene_cameras,144,C.byref(scene_count))
 try:
  assembled=C.string_at(packet,packet_size.value);original=source_packets[0]
  for directory in [60,72]:
   ao,asz=struct.unpack_from('<2I',assembled,directory);bo,bsz=struct.unpack_from('<2I',original,directory)
   assert assembled[ao:ao+asz]==original[bo:bo+bsz],directory
  ao,asz=struct.unpack_from('<2I',assembled,48);bo,bsz=struct.unpack_from('<2I',original,48)
  assert assembled[ao:ao+bsz]==original[bo:bo+bsz]
  assert scene_count.value==len(reconstructed_order)
  (p/'prototype-runs/paired-lifecycle/owned-transition-scene.bin').write_bytes(assembled)
 finally:d.nf_scene_packet_free.argtypes=[P];d.nf_scene_packet_free(packet)
finally:d.nf_close()
report=dict(result='PASS',complete_owned_scene_packet=True,draws=2,retained_after_original_updates=8,distinct_views=owned[0][3]!=owned[1][3],root_view_exact_draw_view=True,owned_root_native_rebuild=True,complete_ordered_root_commands_exact_original=True,original_world_assets_and_lighting_exact=asset_checks,owned_world_metadata_validated=asset_checks,original_model_assets_exact=len(source_models),owned_model_indices_validated=len(source_models),ordered_command_cameras_verified=len(reconstructed_order),epoch_and_ordinal_atomic_rejection=True,scope='Owned root/draw views and concatenated native command kind/source/material order versus original transition packet; GPU multi-view composition incomplete.')
(p/'prototype-runs/paired-lifecycle/draw-view-ownership-test.json').write_text(json.dumps(report,indent=2));print(report)
