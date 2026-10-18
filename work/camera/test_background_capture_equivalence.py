"""Differential bridge test. Never writes to ROM, checkpoint or emulated memory."""
import argparse,ctypes as C,hashlib,json,os,time,struct,traceback
from pathlib import Path
def digest(data): return hashlib.sha256(data).hexdigest()
a=argparse.ArgumentParser()
a.add_argument("--bridge",required=True)
a.add_argument("--runtime",required=True)
a.add_argument("--table",required=True)
a.add_argument("--mode",choices=["full","background"],required=True)
a.add_argument("--frames",type=int,default=600)
a.add_argument("--report",required=True)
a.add_argument("--sky-boundaries",action="store_true")
a.add_argument("--gpu-fixture-dir")
a.add_argument("--scene-timing",action="store_true")
a.add_argument("--pose-boundaries",action="store_true")
args=a.parse_args()
runtime=Path(args.runtime);fixture_done=False
assert not args.pose_boundaries or args.scene_timing,"Pose boundary capture requires optional scene timing"
class Section(C.Structure):_fields_=[("data",C.c_void_p),("size",C.c_size_t)]
class Packet(C.Structure):_fields_=[("serial",C.c_uint32),("begin",C.c_uint32),("end",C.c_uint32),("page",C.c_uint32),("sections",Section*5)]
class Point(C.Structure):_fields_=[("x",C.c_double),("y",C.c_double),("z",C.c_double)]
class Quat(C.Structure):_fields_=[("x",C.c_double),("y",C.c_double),("z",C.c_double),("w",C.c_double)]
class Pose(C.Structure):_fields_=[("position",Point),("rotation",Quat)]
crt=C.CDLL("msvcrt.dll");crt._putenv.argtypes=[C.c_char_p]
for value in (b"NF_LAYER_DIRTY=1",b"NF_TEST_RACING_OWNED_CAPTURE=1"): assert crt._putenv(value)==0
with os.add_dll_directory(str(runtime)),os.add_dll_directory(str(Path(args.bridge).parent)):
 d=C.CDLL(args.bridge)
 d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
 d.nf_native_scene_epoch.restype=C.c_uint64
 d.nf_pixels.restype=C.c_void_p
 d.nf_native_model_plan_trace.argtypes=[C.c_char_p,C.c_void_p,C.c_uint]
 d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_layer_queue_text_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint]
 d.nf_native_live_background_vram.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
 d.nf_native_live_background_coverage.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
 assert d.nf_init(os.fsencode(runtime/"game.gba"),b"")
 try:
  d.nf_60(0);assert d.nf_state(os.fsencode(runtime/"checkpoint.state"),0)
  pose_boundaries=[];pose_missing=[];early_poses={};early_pose_reads=0
  timing_rows=[];timing_checks=0
  packets=[];sky_records=[];sky_objects=[];capture_errors=[]
  if args.sky_boundaries:
   from owned_sky_boundary import SkyBoundary
   from owned_sky_sampler import SkyAsset
   rom=(runtime/"game.gba").read_bytes()
   d.nf_live_completed_sky_read.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
   d.nf_live_completed_sky_identity.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
   d.nf_live_completed_sky_publication_identity.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]

  Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
  def receive(context,epoch,data,size):
   try:
    payload=C.string_at(data,size)
    packets.append([epoch,size,digest(payload)])
    if args.pose_boundaries:
     serial,begin,end=struct.unpack_from("<3I",payload,16)
     buf=C.create_string_buffer(1224)
     if not d.nf_native_scene_pose_boundary_read(epoch,serial,buf,len(buf)):
      pose_missing.append(serial)
     else:
      raw=buf.raw;meta=struct.unpack_from("<16Q",raw)
      source=C.create_string_buffer(1224)
      assert d.nf_native_scene_pose_source_read(epoch,serial,source,len(source))
      source_meta=struct.unpack_from("<16Q",source.raw)
      assert source_meta[:3]==meta[:3] and source_meta[3]==0
      assert source_meta[4:12]==meta[4:12] and source.raw[128:]==raw[128:]
      projection=(C.c_uint32*4)()
      assert d.nf_native_scene_pose_projection_read(epoch,serial,projection)
      assert projection[0]==meta[12]
      detail=(C.c_uint32*28)()
      has_detail=d.nf_native_scene_pose_projection_detail_read(epoch,serial,detail)
      assert bool(has_detail)==bool(projection[3])
      source_clock=(C.c_uint64*3)()
      assert d.nf_native_scene_pose_source_clock_read(epoch,serial,source_clock)
      assert list(source_clock[:2])==list(meta[4:6]) and source_clock[2]<280896
      clock_before=bytes(source_clock)
      assert not d.nf_native_scene_pose_source_clock_read(epoch+1,serial,source_clock) and bytes(source_clock)==clock_before
      assert not d.nf_native_scene_pose_source_clock_read(epoch,serial+16,source_clock) and bytes(source_clock)==clock_before
      prior_pose=early_poses.get(serial)
      if prior_pose:assert prior_pose["raw_hex"]==source.raw.hex()
      assert meta[:4]==(epoch,serial,begin,end) and begin<=meta[5]<=end
      # Owned copy, stale epoch/serial and short-buffer failures are atomic.
      C.memset(buf,77,len(buf))
      assert not d.nf_native_scene_pose_boundary_read(epoch+1,serial,buf,len(buf)) and buf.raw==b"M"*1224
      assert not d.nf_native_scene_pose_boundary_read(epoch,serial+16,buf,len(buf)) and buf.raw==b"M"*1224
      assert not d.nf_native_scene_pose_boundary_read(epoch,serial,buf,len(buf)-1) and buf.raw==b"M"*1224
      assert d.nf_native_scene_pose_boundary_read(epoch,serial,buf,len(buf)) and buf.raw==raw
      packet=Packet();assert d.nf_scene_packet_view(data,size,C.byref(packet))
      cm=(C.c_int32*12).from_buffer_copy(raw[128:176])
      pos=Point(-cm[9],-cm[10],-cm[11]);expected=Pose()
      assert d.nf_pose_decode(cm,C.byref(pos),C.byref(expected))
      decoded=Pose()
      assert d.nf_source_pose_camera(source,len(source),C.byref(decoded)) and bytes(decoded)==bytes(expected)
      cameras=positions=known=pose_orientation_matches=pose_supported=0
      identities=C.string_at(packet.sections[4].data,packet.sections[4].size)
      world=struct.unpack_from("<I",C.string_at(packet.sections[1].data,8),4)[0]
      model_count=d.nf_scene_packet_model_count(C.byref(packet))
      for index in range(model_count):
       section=Section();assert d.nf_scene_packet_model(C.byref(packet),index,C.byref(section))
       model=C.string_at(section.data,section.size)
       cameras+=model[48:104]==bytes(expected)
       object_address=struct.unpack_from("<I",identities,8+(world+index)*20+8)[0]
       object_pose=Pose()
       supported=d.nf_source_pose_object(source,len(source),object_address,sine_table,len(sine_data),C.byref(object_pose))
       pose_supported+=bool(supported)
       if supported:pose_orientation_matches+=(model[104:160]==bytes(object_pose))
       for slot in range(5):
        at=176+slot*208
        if meta[11]&(1<<slot) and struct.unpack_from("<I",raw,at)[0]==object_address:
         known+=1
         xyz=tuple(x/256 for x in struct.unpack_from("<3i",raw,at+16))
         positions+=struct.unpack_from("<3d",model,104)==xyz
      pose_boundaries.append(dict(meta=meta,original_projection_audit=list(projection),original_projection_detail=list(detail) if has_detail else None,source_pose_supported=pose_supported,source_clock=list(source_clock),source_pose_orientations_verified=pose_orientation_matches,raw_hex=raw.hex(),models=model_count,
          packet_camera_matches=cameras,known_packet_objects=known,packet_position_matches=positions))
    if args.scene_timing:
     serial,begin,end=struct.unpack_from("<3I",payload,16)
     row=(C.c_uint64*20)()
     assert d.nf_native_scene_timing_read(epoch,serial,row)
     assert list(row[:4])==[epoch,serial,begin,end]
     assert row[5] and row[5]<=row[6]<=row[4]
     assert begin<=row[19]<=row[18]<=end and sum(row[12:15])>0
     original=list(row);row[0]=0
     assert d.nf_native_scene_timing_read(epoch,serial,row) and list(row)==original
     assert not d.nf_native_scene_timing_read(epoch+1,serial,row) and list(row)==original
     assert not d.nf_native_scene_timing_read(epoch,serial+16,row) and list(row)==original
     timing_rows.append(original)
    if args.sky_boundaries:
     serial,begin,end=struct.unpack_from("<3I",payload,16)
     n=C.c_size_t(0)
     assert d.nf_live_completed_sky_read(epoch,serial,0,None,0,C.byref(n)) and n.value==15192,("missing sky",epoch,serial,begin,end)
     buf=C.create_string_buffer(n.value)
     assert d.nf_live_completed_sky_read(epoch,serial,0,buf,len(buf),C.byref(n))
     boundary=SkyBoundary.decode(buf.raw)
     offset=boundary.asset_origin-0x08000000
     asset=SkyAsset(boundary.asset_origin,rom[offset:offset+15376])
     # Native scene packets permit serial zero. The older SceneSky wrapper
     # additionally requires a closed visibility graph, which this path does not use.
     assert 0<=serial<2**32 and begin<=boundary.refresh<=end
     asset.verify(boundary)
     if args.pose_boundaries and pose_boundaries and pose_boundaries[-1]["meta"][1]==serial:
      source_raw=bytes.fromhex(pose_boundaries[-1]["raw_hex"])
      angle,center=struct.unpack_from("<2I",source_raw,1216)
      signed_center=struct.unpack("<h",struct.pack("<H",center&65535))[0]
      pose_boundaries[-1]["root_sky_angle_matches"]=(angle==boundary.angle)
      pose_boundaries[-1]["root_sky_center_matches"]=(signed_center==boundary.center)
     ident=(C.c_uint32*3)()
     assert d.nf_live_completed_sky_identity(epoch,serial,ident) and list(ident)==[serial,begin,end]
     assert d.nf_live_completed_sky_publication_identity(epoch,end+1,ident) and list(ident)==[serial,begin,end]
     before=buf.raw;sentinel=C.c_size_t(77)
     assert not d.nf_live_completed_sky_read(epoch+1,serial,0,buf,len(buf),C.byref(sentinel))
     assert buf.raw==before and sentinel.value==77
     assert not d.nf_live_completed_sky_read(epoch,serial,1,buf,len(buf),C.byref(sentinel))
     short=C.create_string_buffer(b"x"*64);short_before=short.raw
     assert not d.nf_live_completed_sky_read(epoch,serial,0,short,64,C.byref(sentinel)) and short.raw==short_before
     C.memset(buf,0,len(buf))
     assert d.nf_live_completed_sky_read(epoch,serial,0,buf,len(buf),C.byref(n)) and buf.raw==before
     sky_records.append(dict(epoch=epoch,serial=serial,begin=begin,end=end,copy_refresh=boundary.refresh,angle=boundary.angle,source=boundary.source,asset_origin=boundary.asset_origin,destination=boundary.destination,source_sha256=digest(boundary.indices)))
     sky_objects.append((boundary,asset))
    return 1
   except Exception as error:
    capture_errors.append(dict(traceback=traceback.format_exc(),error=repr(error),serial=locals().get("serial"),begin=locals().get("begin"),end=locals().get("end"),copy_refresh=getattr(locals().get("boundary"),"refresh",None)));return 0
  sink=Sink(receive);d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
  assert d.nf_native_scene_sink(sink,None);assert d.nf_native_scene_multimodel(1)
  timing_default_off_checked=False
  if hasattr(d,"nf_native_scene_timing_read"):
   d.nf_native_scene_timing_read.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_uint64)]
   sentinel=(C.c_uint64*20)(*([77]*20))
   assert not d.nf_native_scene_timing_read(d.nf_native_scene_epoch(),0,sentinel) and list(sentinel)==[77]*20
   if hasattr(d,"nf_native_scene_pose_source_read"):
    d.nf_native_scene_pose_source_read.argtypes=[C.c_uint64,C.c_uint32,C.c_void_p,C.c_size_t]
    pose_sentinel=C.create_string_buffer(b"M"*1224)
    assert not d.nf_native_scene_pose_source_read(d.nf_native_scene_epoch(),0,pose_sentinel,1224) and pose_sentinel.raw==b"M"*1224+b"\0"
   timing_default_off_checked=True
  if args.scene_timing:
   d.nf_native_scene_timing_read.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_uint64)]
   assert d.nf_native_scene_timing_enable(1)
  if args.pose_boundaries:
   d.nf_native_scene_pose_boundary_read.argtypes=[C.c_uint64,C.c_uint32,C.c_void_p,C.c_size_t]
   d.nf_native_scene_pose_source_read.argtypes=[C.c_uint64,C.c_uint32,C.c_void_p,C.c_size_t]
   d.nf_native_scene_pose_source_clock_read.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_uint64)]
   d.nf_source_pose_camera.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Pose)]
   d.nf_source_pose_object.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t,C.POINTER(Pose)]
   d.nf_native_scene_pose_projection_read.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_uint32)]
   d.nf_native_scene_pose_projection_detail_read.argtypes=[C.c_uint64,C.c_uint32,C.POINTER(C.c_uint32)]
   sine_data=(runtime/"game.gba").read_bytes()[0x623700:0x627700]
   sine_table=C.create_string_buffer(sine_data)
   d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
   d.nf_scene_packet_model_count.argtypes=[C.POINTER(Packet)]
   d.nf_scene_packet_model.argtypes=[C.POINTER(Packet),C.c_uint,C.POINTER(Section)]
   d.nf_pose_decode.argtypes=[C.POINTER(C.c_int32),C.POINTER(Point),C.POINTER(Pose)]
  assert d.nf_layer_queue_enable(1);assert d.nf_bitmap_text_enable(1)
  fast=int(args.mode=="background")
  mode_fn=getattr(d,"nf_native_background_capture_only",None)
  if mode_fn: assert mode_fn(fast)
  else: assert not fast, "Bridge does not support background-only capture"
  data=Path(args.table).read_bytes();table=C.create_string_buffer(data)
  assert d.nf_native_model_plan_trace(b"",table,len(data));assert d.nf_world_trace(b"")
  if args.sky_boundaries: assert d.nf_live_sky_capture_enable(1)
  # Changing capture semantics while enabled must fail without altering it.
  if mode_fn: assert not mode_fn(1-fast)
  hudsize=d.nf_layer_hud_row_size();hud=C.create_string_buffer(hudsize*160)
  text=C.create_string_buffer(76800)
  vram=C.create_string_buffer(0x18000);coverage=C.create_string_buffer(0x18000)
  pixels=[];backgrounds=[];rows=[];prior=0;core_ms=[]
  for i in range(args.frames):
   keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
   start=time.perf_counter();d.nf_frame(keys);core_ms.append((time.perf_counter()-start)*1000)
   if args.pose_boundaries:
    stats=(C.c_uint32*4)();d.nf_native_scene_stats(stats)
    source=C.create_string_buffer(1224);epoch=d.nf_native_scene_epoch()
    if d.nf_native_scene_pose_source_read(epoch,stats[0],source,len(source)):
     meta=struct.unpack_from("<16Q",source.raw)
     assert meta[0]==epoch and meta[1]==stats[0] and meta[3]==0 and meta[11]==31
     source_clock=(C.c_uint64*3)()
     assert d.nf_native_scene_pose_source_clock_read(epoch,stats[0],source_clock)
     assert list(source_clock[:2])==list(meta[4:6]) and source_clock[2]<280896
     previous_source=source.raw
     assert not d.nf_native_scene_pose_boundary_read(epoch,stats[0],source,len(source)) and source.raw==previous_source
     serial=stats[0];prior_pose=early_poses.get(serial)
     if prior_pose:assert prior_pose["raw_hex"]==source.raw.hex() and prior_pose["source_clock"]==list(source_clock)
     else:early_poses[serial]=dict(raw_hex=source.raw.hex(),source_clock=list(source_clock),first_available_refresh=d.nf_native_scene_refresh(),source_refresh=meta[5])
     early_pose_reads+=1
     previous=source.raw
     assert not d.nf_native_scene_pose_source_read(epoch+1,serial,source,len(source)) and source.raw==previous
     assert not d.nf_native_scene_pose_source_read(epoch,serial+16,source,len(source)) and source.raw==previous
     assert not d.nf_native_scene_pose_source_read(epoch,serial,source,len(source)-1) and source.raw==previous
   pixels.append(digest(C.string_at(d.nf_pixels(),240*160*4)))
   refresh=d.nf_native_live_latest_frame()
   if refresh and refresh!=prior:
    assert d.nf_native_live_background_vram(refresh,vram,len(vram))
    assert d.nf_native_live_background_coverage(refresh,coverage,len(coverage))
    mask=coverage.raw
    assert set(mask)<={0,1}
    owned=bytes(value if mask[j] else 0 for j,value in enumerate(vram.raw))
    backgrounds.append([refresh,digest(mask+owned),sum(mask)]);prior=refresh
   if i%8==7:
    epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest()
    for y in range(160):
     assert d.nf_layer_queue_hud_row(epoch,refresh,y,C.byref(hud,y*hudsize),hudsize)
     assert d.nf_layer_queue_text_row(epoch,refresh,y,C.byref(text,y*240),C.byref(text,38400+y*240),240)
    rows.append([epoch,refresh,digest(hud.raw+text.raw)])
    if args.gpu_fixture_dir and not fixture_done and len(sky_objects)>=2:
     old,asset=sky_objects[-2];new,_=sky_objects[-1]
     if old.angle!=new.angle and old.asset_origin==new.asset_origin:
      folder=Path(args.gpu_fixture_dir);folder.mkdir(parents=True,exist_ok=True)
      (folder/"old.nfsk").write_bytes(old.encode());(folder/"new.nfsk").write_bytes(new.encode());(folder/"asset.bin").write_bytes(asset.data)
      raw=hud.raw
      palettes=b"".join(raw[y*hudsize+32896:y*hudsize+32896+512] for y in range(160))
      (folder/"palettes.bin").write_bytes(palettes)
      first,last=sky_records[-2:]
      (folder/"pair.bin").write_bytes(struct.pack("<Q6I",first["epoch"],first["serial"],first["begin"],first["end"],last["serial"],last["begin"],last["end"]))
      fixture_done=True

  assert not capture_errors,capture_errors[:4]
  if args.gpu_fixture_dir:assert fixture_done,"No moving sky pair for GPU fixture"
  fractional_samples=0
  for (old,asset),(new,_) in zip(sky_objects,sky_objects[1:]):
   if old.epoch!=new.epoch or old.asset_origin!=new.asset_origin:continue
   assert asset.sample(old,new,0).lower==old.indices
   assert asset.sample(old,new,1).lower==new.indices
   for alpha in (.25,.5,.75):
    sample=asset.sample_continuous(old,new,alpha)
    assert len(sample.lower)==len(sample.upper)==15136 and 0<=sample.weight<1
    fractional_samples+=1
  if args.pose_boundaries:
   assert pose_boundaries,"No source-root poses observed"
   first=pose_boundaries[0]["meta"];last=pose_boundaries[-1]["meta"]
   sentinel=C.create_string_buffer(b"M"*1224)
   assert not d.nf_native_scene_pose_boundary_read(first[0],first[1],sentinel,1224) and sentinel.raw==b"M"*1224+b"\0"
   assert not d.nf_native_scene_pose_source_read(first[0],first[1],sentinel,1224) and sentinel.raw==b"M"*1224+b"\0"
   stale_clock=(C.c_uint64*3)(77,77,77)
   assert not d.nf_native_scene_pose_source_clock_read(first[0],first[1],stale_clock) and list(stale_clock)==[77]*3
  if args.scene_timing:
   assert len(timing_rows)==len(packets)>16
   row=(C.c_uint64*20)(*([77]*20));first=timing_rows[0]
   assert not d.nf_native_scene_timing_read(first[0],first[1],row) and list(row)==[77]*20
   assert not d.nf_native_scene_timing_enable(0), "Cannot change observer mid-scene"
   last=timing_rows[-1];d.nf_native_scene_discontinuity()
   assert not d.nf_native_scene_timing_read(last[0],last[1],row) and list(row)==[77]*20
   timing_checks=len(timing_rows)*4+3
  if args.pose_boundaries:
   assert not d.nf_native_scene_pose_boundary_read(last[0],last[1],sentinel,1224) and sentinel.raw==b"M"*1224+b"\0"
   assert not d.nf_native_scene_pose_source_read(last[0],last[1],sentinel,1224) and sentinel.raw==b"M"*1224+b"\0"
   assert not d.nf_native_scene_pose_source_clock_read(last[0],last[1],stale_clock) and list(stale_clock)==[77]*3
  if args.sky_boundaries:
   assert len(sky_records)==len(packets) and sky_records
   first=sky_records[0];n=C.c_size_t(77)
   # History eviction must not expose another serial in the same ring slot.
   assert not d.nf_live_completed_sky_read(first["epoch"],first["serial"],0,None,0,C.byref(n)) and n.value==77
   last=sky_records[-1];d.nf_native_scene_discontinuity()
   assert not d.nf_live_completed_sky_read(last["epoch"],last["serial"],0,None,0,C.byref(n)) and n.value==77
  result=dict(early_pose_reads=early_pose_reads,early_poses=early_poses,pose_boundaries=pose_boundaries,pose_boundary_missing=pose_missing,scene_timing_default_off_checked=timing_default_off_checked,scene_timing=timing_rows,scene_timing_checks=timing_checks,sky_boundaries=sky_records,sky_fractional_component_samples=fractional_samples,mode=args.mode,frames=args.frames,packets=packets,original_frame_hashes=pixels,backgrounds=backgrounds,hud_text_samples=rows,core_mean_ms=sum(core_ms)/len(core_ms),core_max_ms=max(core_ms),scope="Unpaced deterministic differential capture, not display pacing or full-course validation")
  Path(args.report).write_text(json.dumps(result,indent=2))
  print(json.dumps({k:v for k,v in result.items() if k not in ("packets","original_frame_hashes","backgrounds","hud_text_samples","sky_boundaries","scene_timing","pose_boundaries","early_poses")}))
  print("packets",len(packets),"backgrounds",len(backgrounds),"HUD/text",len(rows))
 finally: d.nf_close()
