"""Real native packet/HUD ownership after bridge eviction and checkpoint reload."""
from pathlib import Path
import ctypes as C,json,struct,hashlib,uuid,sys
p=Path(__file__).resolve().parent;P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
class Identity(C.Structure):_fields_=[('epoch',C.c_uint64)]+[(k,U) for k in ('serial','begin','end','query','builder')]
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);Read=C.CFUNCTYPE(C.c_int,P,C.c_uint64,U,C.c_uint,P)
d=C.CDLL(str(p/'visibility-probe-wide.dll'));b=C.CDLL(str(p/'presentation-submission.dll'))
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,P];d.nf_live_visibility_enable.argtypes=[P,Z,Z]
d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,U,C.c_uint,P,C.c_uint];d.nf_layer_queue_zero_colors.argtypes=[C.c_uint64,U,P,C.c_uint];d.nf_scene_packet_free.argtypes=[P]
pair=d.nf_live_completed_native_multimodel_world_classified_pair_packet;pair.argtypes=[P,P,C.c_double,P,P,P]
b.nf_submission_create.argtypes=[P,Z,P,U,U,P,P,Read,P,P];b.nf_submission_destroy.argtypes=[P];b.nf_submission_row.argtypes=[P,C.c_uint64,U,C.c_uint,P];b.nf_submission_packet.argtypes=[P,P,P];b.nf_submission_time.argtypes=[P];b.nf_submission_time.restype=P
b.nf_submission_sources.argtypes=[P,P]
b.nf_submission_cameras.argtypes=[P];b.nf_submission_cameras.restype=P;b.nf_submission_zero_colors.argtypes=[P];b.nf_submission_zero_colors.restype=P
b.nf_submission_clone.argtypes=[P];b.nf_submission_clone.restype=P;b.nf_submission_poison_retired.argtypes=[P];b.nf_submission_difference.argtypes=[P,P]
identities=[]
@Sink
def sink(ctx,epoch,data,size):
 header=struct.unpack_from('<8I',C.string_at(data,32));identities.append(Identity(epoch,*header[4:7],0,0));return 1
@Read
def reader(ctx,epoch,refresh,y,out):return d.nf_layer_queue_hud_row(epoch,refresh,y,out,34944)
take_mode='--take' in sys.argv;release_calls=[]
Release=C.CFUNCTYPE(None,P)
@Release
def release_owned(packet):release_calls.append(packet);d.nf_scene_packet_free(packet)
b.nf_submission_take.argtypes=[C.POINTER(P),Z,P,U,U,P,P,Read,P,Release,P]
out=P();frame_count=0;report_path=p/('presentation-submission-take-tests.json' if take_mode else 'presentation-submission-tests.json');report_path.write_text(json.dumps(dict(result='RUNNING')))
handoff_report=p/'submission-handoff-tests.json';handoff_report.write_text(json.dumps(dict(result='RUNNING')))
def failure_hook(kind,error,trace):
 handoff_report.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2))
 report_path.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));sys.__excepthook__(kind,error,trace)
sys.excepthook=failure_hook
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 raw_rom=rom.read_bytes();assert d.nf_live_visibility_enable(raw_rom,len(raw_rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_layer_queue_enable(1)
 while len(identities)<2 and frame_count<60:d.nf_frame(1);frame_count+=1
 assert len(identities)>=2
 a,c=identities[-2:];sample=Time(c.epoch,a.serial,c.serial,.5,(a.end+c.end)/2);selected=int(sample.target)
 packet=P();size=Z();stage=U();assert pair(C.byref(a),C.byref(c),.5,C.byref(packet),C.byref(size),C.byref(stage)),stage.value
 packet_bytes=C.string_at(packet,size.value);zero=(C.c_uint16*160)();assert d.nf_layer_queue_zero_colors(sample.epoch,selected,zero,320)
 if take_mode:
  original_address=packet.value;assert b.nf_submission_take(C.byref(packet),size.value,C.byref(sample),a.end,c.end,None,zero,reader,None,release_owned,C.byref(out)) and packet.value is None
 else:
  try:assert b.nf_submission_create(packet,size.value,C.byref(sample),a.end,c.end,None,zero,reader,None,C.byref(out))
  finally:d.nf_scene_packet_free(packet)
 # Per-command camera pairs are sampled once into immutable owned poses.
 pair_submission=b.nf_submission_clone(out);assert pair_submission
 import math
 b.nf_submission_command_camera_pair_set.argtypes=[P,P,P,U];b.nf_submission_command_cameras.argtypes=[P,P,P]
 section_offset=struct.unpack_from('<I',packet_bytes,60)[0];commands=struct.unpack_from('<I',packet_bytes,section_offset+4)[0]
 aa=(C.c_double*(commands*7))();bb=(C.c_double*(commands*7))()
 for j in range(commands):
  aa[j*7:j*7+7]=[j,0,0,0,0,0,1];bb[j*7:j*7+7]=[j+10,4,-2,0,0,math.sin(math.pi/4),math.cos(math.pi/4)]
 bad=(C.c_double*(commands*7))(*bb);bad[(commands-1)*7]=float('nan');absent=P(123);absent_count=U(999)
 assert not b.nf_submission_command_camera_pair_set(pair_submission,aa,bad,commands)
 assert not b.nf_submission_command_cameras(pair_submission,C.byref(absent),C.byref(absent_count)) and absent.value==123 and absent_count.value==999
 assert not b.nf_submission_command_camera_pair_set(pair_submission,aa,bb,commands-1)
 assert b.nf_submission_command_camera_pair_set(pair_submission,aa,bb,commands) and not b.nf_submission_command_camera_pair_set(pair_submission,aa,bb,commands)
 owned=P();owned_count=U();assert b.nf_submission_command_cameras(pair_submission,C.byref(owned),C.byref(owned_count)) and owned_count.value==commands
 values=struct.unpack('<'+str(commands*7)+'d',C.string_at(owned,commands*56));t=sample.alpha
 for j in range(commands):
  expected=[j+10*t,4*t,-2*t,0,0,math.sin(math.pi*t/4),math.cos(math.pi*t/4)];assert max(abs(x-y) for x,y in zip(values[j*7:j*7+7],expected))<1e-12
 C.memset(aa,165,C.sizeof(aa));C.memset(bb,165,C.sizeof(bb));assert C.string_at(owned,commands*56)==struct.pack('<'+str(commands*7)+'d',*values)
 b.nf_submission_destroy(pair_submission)
 # Complete immutable text transport, atomic rejection and independent clone.
 TextRead=C.CFUNCTYPE(C.c_int,P,C.c_uint64,U,C.c_uint,P,P)
 b.nf_submission_text_capture.argtypes=[P,TextRead,P];b.nf_submission_text_row.argtypes=[P,C.c_uint64,U,C.c_uint,P,P]
 text_mode=[0]
 @TextRead
 def text_reader(ctx,epoch,refresh,y,indices,coverage):
  if text_mode[0]==0 and y==80:return 0
  C.memset(indices,y,240);C.memset(coverage,1,240)
  if text_mode[0]==1 and y==80:C.memset(coverage,2,1)
  return 1
 text_indices=C.create_string_buffer(b'Q'*240,240);text_coverage=C.create_string_buffer(b'R'*240,240)
 assert not b.nf_submission_text_capture(out,text_reader,None)
 assert not b.nf_submission_text_row(out,sample.epoch,selected,0,text_indices,text_coverage) and text_indices.raw==b'Q'*240 and text_coverage.raw==b'R'*240
 text_mode[0]=1;assert not b.nf_submission_text_capture(out,text_reader,None)
 text_mode[0]=2;assert b.nf_submission_text_capture(out,text_reader,None) and not b.nf_submission_text_capture(out,text_reader,None)
 text_clone=b.nf_submission_clone(out);assert text_clone and b.nf_submission_difference(out,text_clone)==0
 for y in [0,80,159]:assert b.nf_submission_text_row(text_clone,sample.epoch,selected,y,text_indices,text_coverage) and text_indices.raw==bytes([y])*240 and text_coverage.raw==bytes([1])*240
 assert not b.nf_submission_text_row(text_clone,sample.epoch+1,selected,0,text_indices,text_coverage)
 b.nf_submission_destroy(text_clone)
 saved_time=C.string_at(C.byref(sample),C.sizeof(sample));saved_rows=[];row=C.create_string_buffer(34944)
 sources=(U*2)();assert b.nf_submission_sources(out,sources) and list(sources)==[a.end,c.end]
 for y in range(160):assert b.nf_submission_row(out,sample.epoch,selected,y,row);saved_rows.append(row.raw)
 b.nf_submission_bg_palettes.argtypes=[P,C.c_uint64,U,P]
 palette_output=C.create_string_buffer(b'\xa5'*81920,81920)
 for owner,epoch,refresh in [(None,sample.epoch,selected),(out,sample.epoch+1,selected),(out,sample.epoch,selected+1)]:
  assert not b.nf_submission_bg_palettes(owner,epoch,refresh,palette_output) and palette_output.raw==b'\xa5'*81920
 assert b.nf_submission_bg_palettes(out,sample.epoch,selected,palette_output)
 expected_palettes=b''.join(r[32896:32896+512] for r in saved_rows)
 assert palette_output.raw==expected_palettes
 borrowed=P();borrowed_size=Z();assert b.nf_submission_packet(out,C.byref(borrowed),C.byref(borrowed_size));assert C.string_at(borrowed,borrowed_size.value)==packet_bytes
 # Reject a missing row and inconsistent index-zero color atomically.
 source=C.create_string_buffer(packet_bytes,len(packet_bytes));sentinel=P(123)
 @Read
 def missing(ctx,epoch,refresh,y,target):return 0 if y==80 else reader(ctx,epoch,refresh,y,target)
 assert not b.nf_submission_create(source,len(packet_bytes),C.byref(sample),a.end,c.end,None,zero,missing,None,C.byref(sentinel)) and sentinel.value==123
 if take_mode:
  fail_packet=P(C.addressof(source));fail_address=fail_packet.value
  assert not b.nf_submission_take(C.byref(fail_packet),len(packet_bytes),C.byref(sample),a.end,c.end,None,zero,missing,None,release_owned,C.byref(sentinel)) and fail_packet.value==fail_address and sentinel.value==123 and not release_calls
 # Camera/zero-color input ownership, using explicit component camera values.
 cameras=(C.c_double*14)(1,2,3,0,0,0,1,-4,5,6,0,0,0,1);saved_cameras=bytes(cameras);saved_zero=bytes(zero);camera_bundle=P()
 assert b.nf_submission_create(source,len(packet_bytes),C.byref(sample),a.end,c.end,cameras,zero,reader,None,C.byref(camera_bundle))
 clone=b.nf_submission_clone(camera_bundle);assert clone and b.nf_submission_difference(camera_bundle,clone)==0
 C.memset(cameras,0,C.sizeof(cameras));zero[0]^=1
 assert C.string_at(b.nf_submission_cameras(camera_bundle),112)==saved_cameras and C.string_at(b.nf_submission_zero_colors(camera_bundle),320)==saved_zero
 b.nf_submission_poison_retired(camera_bundle);assert b.nf_submission_difference(camera_bundle,clone)==3
 assert b.nf_submission_row(clone,sample.epoch,selected,159,row) and row.raw==saved_rows[159]
 assert b.nf_submission_bg_palettes(clone,sample.epoch,selected,palette_output) and palette_output.raw==expected_palettes
 b.nf_submission_destroy(camera_bundle);b.nf_submission_destroy(clone);zero[0]^=1
 zero[90]^=1
 assert not b.nf_submission_create(source,len(packet_bytes),C.byref(sample),a.end,c.end,None,zero,reader,None,C.byref(sentinel)) and sentinel.value==123
 zero[90]^=1
 # Schedule is copied exactly once before publication, not a borrowed clock.
 class Schedule(C.Structure):_fields_=[('origin',C.c_uint64),('lag',C.c_uint64),('base',U),('delay',C.c_double)]
 b.nf_submission_schedule_set.argtypes=[P,C.POINTER(Schedule)];b.nf_submission_schedule_get.argtypes=[P,C.POINTER(Schedule)]
 timing=Schedule(123000000,16666667,a.end,8);saved_timing=bytes(timing)
 assert b.nf_submission_schedule_set(out,C.byref(timing))
 timing.origin=999;timing.base=0
 assert not b.nf_submission_schedule_set(out,C.byref(timing))
 copied=Schedule();assert b.nf_submission_schedule_get(out,C.byref(copied)) and bytes(copied)==saved_timing
 # Per-command cameras are copied, validated once and survive source mutation.
 b.nf_submission_command_cameras_set.argtypes=[P,P,U];b.nf_submission_command_cameras.argtypes=[P,P,P]
 order_offset=struct.unpack_from('<I',packet_bytes,60)[0];command_count=struct.unpack_from('<I',packet_bytes,order_offset+4)[0]
 command_cameras=(C.c_double*(command_count*7))()
 for k in range(command_count):
  for j,v in enumerate((float(k),2.,3.,0.,0.,0.,1.)):command_cameras[k*7+j]=v
 before=P(123);before_count=U(123);assert not b.nf_submission_command_cameras(out,C.byref(before),C.byref(before_count)) and before.value==123 and before_count.value==123
 assert not b.nf_submission_command_cameras_set(out,command_cameras,command_count-1)
 command_cameras[0]=float('nan');assert not b.nf_submission_command_cameras_set(out,command_cameras,command_count);command_cameras[0]=0
 assert b.nf_submission_command_cameras_set(out,command_cameras,command_count)
 saved_commands=bytes(command_cameras);C.memset(command_cameras,165,C.sizeof(command_cameras))
 assert not b.nf_submission_command_cameras_set(out,command_cameras,command_count)
 assert b.nf_submission_command_cameras(out,C.byref(before),C.byref(before_count)) and before_count.value==command_count and C.string_at(before,command_count*56)==saved_commands
 timed_clone=b.nf_submission_clone(out);assert timed_clone and b.nf_submission_schedule_get(timed_clone,C.byref(copied)) and bytes(copied)==saved_timing and b.nf_submission_difference(out,timed_clone)==0
 b.nf_submission_destroy(timed_clone)
 # Bounded handoff: actual simultaneous producer/consumer with real frame bytes.
 import threading,time
 b.nf_handoff_create.argtypes=[C.c_uint64];b.nf_handoff_create.restype=P
 b.nf_handoff_push.argtypes=[P,C.POINTER(P)];b.nf_handoff_pop.argtypes=[P];b.nf_handoff_pop.restype=P
 b.nf_handoff_epoch.argtypes=[P,C.c_uint64];b.nf_handoff_close.argtypes=[P];b.nf_handoff_destroy.argtypes=[P]
 q=b.nf_handoff_create(sample.epoch);assert q
 errors=[];received=[]
 def consume():
  try:
   while len(received)<100:
    item=b.nf_handoff_pop(q)
    if not item:time.sleep(.001);continue
    try:assert b.nf_submission_difference(out,item)==0;received.append(item)
    finally:b.nf_submission_destroy(item)
  except BaseException as e:errors.append(repr(e))
 worker=threading.Thread(target=consume);worker.start()
 for i in range(100):
  item=P(b.nf_submission_clone(out));assert item.value
  deadline=time.monotonic()+10
  while not b.nf_handoff_push(q,C.byref(item)):
   assert not errors and time.monotonic()<deadline;time.sleep(.001)
  assert not item.value
 worker.join(10);assert not worker.is_alive() and not errors and len(received)==100
 # Capacity rejection preserves caller ownership; epoch retirement leaves popped data alive.
 for i in range(3):
  item=P(b.nf_submission_clone(out));assert b.nf_handoff_push(q,C.byref(item)) and not item.value
 rejected=P(b.nf_submission_clone(out));saved=rejected.value
 assert not b.nf_handoff_push(q,C.byref(rejected)) and rejected.value==saved
 held=b.nf_handoff_pop(q);assert held
 assert b.nf_handoff_epoch(q,sample.epoch+1) and not b.nf_handoff_pop(q)
 assert b.nf_submission_difference(out,held)==0
 assert not b.nf_handoff_push(q,C.byref(rejected)) and rejected.value==saved
 assert not b.nf_handoff_epoch(q,sample.epoch)
 Present=C.CFUNCTYPE(C.c_int,P);commits=[]
 @Present
 def present(ctx):commits.append(1);return 1
 b.nf_handoff_commit.argtypes=[P,C.c_uint64,Present,P];b.nf_handoff_invalidate.argtypes=[P]
 b.nf_handoff_current_epoch.argtypes=[P];b.nf_handoff_current_epoch.restype=C.c_uint64
 assert b.nf_handoff_commit(q,sample.epoch+1,present,None)==1 and len(commits)==1
 b.nf_handoff_invalidate(q);assert b.nf_handoff_current_epoch(q)==0
 assert b.nf_handoff_commit(q,sample.epoch+1,present,None)==0 and len(commits)==1
 assert not b.nf_handoff_epoch(q,sample.epoch+1)
 assert b.nf_handoff_epoch(q,sample.epoch+2) and b.nf_handoff_commit(q,sample.epoch+2,present,None)==1 and len(commits)==2
 b.nf_handoff_close(q);assert not b.nf_handoff_epoch(q,sample.epoch+2)
 assert not b.nf_handoff_push(q,C.byref(rejected)) and rejected.value==saved
 b.nf_submission_destroy(held);b.nf_submission_destroy(rejected);b.nf_handoff_destroy(q)
 (p/'submission-handoff-tests.json').write_text(json.dumps(dict(result='PASS',concurrent_real_frame_transfers=100,capacity=3,full_rejection_preserves_owner=True,epoch_drains_pending_only=True,stale_epoch_rejected=True,scope='Real complete packet/HUD bytes transferred across producer/consumer threads; no GL worker, presentation timing or smooth60fps proof.'),indent=2))
 # Advance beyond the sixteen-refresh layer history and scene history.
 for i in range(40):d.nf_frame(1);frame_count+=1
 assert not d.nf_layer_queue_hud_row(sample.epoch,selected,0,row,34944)
 assert d.nf_state(str(p.parent/'driving.state').encode(),0)
 for i in range(4):d.nf_frame(1)
 for y in range(160):assert b.nf_submission_row(out,sample.epoch,selected,y,row) and row.raw==saved_rows[y]
 assert C.string_at(borrowed,borrowed_size.value)==packet_bytes and C.string_at(b.nf_submission_time(out),C.sizeof(sample))==saved_time
 unchanged=row.raw;assert not b.nf_submission_row(out,sample.epoch+1,selected,0,row) and row.raw==unchanged
 actual=[];run=p/'prototype-runs'/('submission-'+uuid.uuid4().hex);d.nf_dump.argtypes=[C.c_char_p,U,U]
 for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=Path(str(run)+'-'+name+'.bin');d.nf_dump(str(path).encode(),base,n);actual.append(path.read_bytes())
finally:
 b.nf_submission_destroy(out)
 if take_mode:assert release_calls==[original_address],release_calls
 d.nf_close()
baseline=C.CDLL(str(p.parent/'nfsprobe.dll'));baseline.nf_init.argtypes=[C.c_char_p]*2;baseline.nf_state.argtypes=[C.c_char_p,C.c_int];baseline.nf_dump.argtypes=[C.c_char_p,U,U]
assert baseline.nf_init(str(rom).encode(),b'') and baseline.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for i in range(4):baseline.nf_frame(1)
 for expected,(name,base,n) in zip(actual,[('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]):
  path=Path(str(run)+'-baseline-'+name+'.bin');baseline.nf_dump(str(path).encode(),base,n);assert path.read_bytes()==expected
finally:baseline.nf_close()
report=dict(result='PASS',exclusive_packet_take=take_mode,transfer_failure_atomic=take_mode,release_exactly_once=take_mode,native_packet_bytes=len(packet_bytes),owned_hud_rows_exact=160,camera_and_zero_input_mutation_isolated=True,schedule_input_mutation_isolated=True,schedule_clone_exact=True,command_cameras_owned=command_count,command_camera_invalid_and_count_rejected=True,command_camera_clone_handoff_exact=True,retired_original_clone_exact=True,original_updates_before_reload=frame_count,bridge_source_evicted=True,checkpoint_reload_survived=True,atomic_rejections=3,final_ram_parity=True,scope='Owned real paired native packet, selected exact HUD rows and timeline metadata survive forty subsequent original updates and read-only checkpoint reload. Component camera values test input ownership, not recovered camera accuracy. Full final RAM compared to original bridge after same reload/four inputs. Component and same-thread ownership proof, not concurrent GL presentation or smooth60fps.')
report_path.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


