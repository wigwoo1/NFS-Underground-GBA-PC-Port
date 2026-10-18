"""Detached compact hardware snapshot survives updates, eviction and reload."""
import ctypes as C,hashlib,json,threading
from pathlib import Path
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_clone.argtypes=[C.c_uint64,C.c_uint];d.nf_layer_queue_clone.restype=P;d.nf_layer_snapshot_read.argtypes=[P,C.c_uint,P];d.nf_layer_snapshot_destroy.argtypes=[P];d.nf_layer_snapshot_bytes.argtypes=[P];d.nf_layer_snapshot_bytes.restype=C.c_size_t;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,P,C.c_uint];rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';h=C.CDLL(str(p/'hardware-submission.dll'))
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Schedule(C.Structure):_fields_=[('origin',C.c_uint64),('lag',C.c_uint64),('base',C.c_uint32),('delay',C.c_double)]
h.nf_hardware_submission_create.argtypes=[P,C.POINTER(Time),C.POINTER(Schedule),C.POINTER(P)];h.nf_hardware_submission_destroy.argtypes=[P];h.nf_hardware_submission_row.argtypes=[P,C.c_uint64,C.c_uint,C.c_uint,P];h.nf_hardware_submission_bytes.argtypes=[P];h.nf_hardware_submission_bytes.restype=C.c_size_t;h.nf_hardware_submission_metadata.argtypes=[P,C.POINTER(Time),C.POINTER(Schedule)]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,C.c_size_t)
@Sink
def sink(ctx,epoch,data,size):return 1
d.nf_native_scene_sink.argtypes=[Sink,P]
checks=[]
for name in ['stage-0','stage-2','menu-4','menu-5']:
 state=p.parent/'fix-menu'/(name+'.state');state_hash=hashlib.sha256(state.read_bytes()).hexdigest();snapshot=None;submission=P()
 assert d.nf_init(rom,b'') and d.nf_state(str(state).encode(),0) and d.nf_native_scene_sink(sink,None) and d.nf_layer_queue_enable(1)
 try:
  for _ in range(40):d.nf_frame(0)
  epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest();assert not d.nf_layer_queue_clone(epoch+1,refresh) and not d.nf_layer_queue_clone(epoch,refresh+100)
  snapshot=d.nf_layer_queue_clone(epoch,refresh);assert snapshot;buf=C.create_string_buffer(100480);hashes=[]
  for y in range(160):assert d.nf_layer_snapshot_read(snapshot,y,buf);hashes.append(hashlib.sha256(buf.raw).hexdigest())
  time=Time(epoch,refresh,refresh,0,refresh+.25);schedule=Schedule(1000,33333334,refresh,8);sentinel=P(123)
  time.target=refresh+1;assert not h.nf_hardware_submission_create(snapshot,C.byref(time),C.byref(schedule),C.byref(sentinel)) and sentinel.value==123
  time.target=refresh+.25;assert h.nf_hardware_submission_create(snapshot,C.byref(time),C.byref(schedule),C.byref(submission))
  size=h.nf_hardware_submission_bytes(submission);saved_time=bytes(time);saved_schedule=bytes(schedule);time.target=0;schedule.origin=0
  actual_time=Time();actual_schedule=Schedule();assert h.nf_hardware_submission_metadata(submission,C.byref(actual_time),C.byref(actual_schedule)) and bytes(actual_time)==saved_time and bytes(actual_schedule)==saved_schedule
  d.nf_layer_snapshot_destroy(snapshot);snapshot=None
  for _ in range(40):d.nf_frame(0)
  assert not d.nf_layer_queue_row(epoch,refresh,0,buf,100480)
  assert d.nf_state(str(state).encode(),0)
  error=[]
  def consumer():
   try:
    local=C.create_string_buffer(100480)
    for y in range(160):assert h.nf_hardware_submission_row(submission,epoch,refresh,y,local) and hashlib.sha256(local.raw).hexdigest()==hashes[y]
   except BaseException as e:error.append(str(e))
  worker=threading.Thread(target=consumer);worker.start()
  for _ in range(8):d.nf_frame(0)
  worker.join();assert not error,error
  sentinel=C.create_string_buffer(b'Q'*100480,100480);assert not h.nf_hardware_submission_row(submission,epoch+1,refresh,0,sentinel) and sentinel.raw==b'Q'*100480
  assert not h.nf_hardware_submission_row(submission,epoch,refresh,160,sentinel) and sentinel.raw==b'Q'*100480
  checks.append(dict(checkpoint=name,epoch=epoch,refresh=refresh,owned_bytes=size,expanded_row_bytes=160*100480,rows_exact_after_eviction_reload=160,concurrent_original_updates=8,invalid_epoch_refresh_rejected=True,invalid_row_atomic=True));print(name,size,flush=True)
 finally:
  if snapshot:d.nf_layer_snapshot_destroy(snapshot)
  h.nf_hardware_submission_destroy(submission)
  d.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==state_hash
out=p/'prototype-runs/lifecycle-hardware/hardware-submission-report.json';out.write_text(json.dumps(dict(result='PASS',checks=checks,scope='Detached compact sourcehardware pages survive queueeviction/checkpointreload and concurrent consumer reads during8originalupdates. No borrowed bridgeviews; tests read-only. Copied immutable timeline/schedule validated; not yet threadedGL integration or native4K menus.'),indent=2))
