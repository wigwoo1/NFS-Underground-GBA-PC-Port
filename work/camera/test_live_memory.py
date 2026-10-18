from pathlib import Path
import ctypes as C,struct,json,hashlib
root=Path('work').resolve();d=C.CDLL(str(root/'nfsprobe.dll'))
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Pair(C.Structure):_fields_=[('time',Time),('older',C.c_void_p),('older_size',C.c_size_t),('newer',C.c_void_p),('newer_size',C.c_size_t)]
P=C.c_void_p;Z=C.c_size_t;Q=C.c_uint64
Sink=C.CFUNCTYPE(C.c_int,P,Q,P,Z)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,P];d.nf_native_scene_epoch.restype=Q
d.nf_snapshot_create.argtypes=[Z];d.nf_snapshot_create.restype=P
d.nf_scene_packet_push.argtypes=[P,Q,P,Z]
d.nf_snapshot_acquire.argtypes=[P,C.c_double,C.c_double,C.POINTER(Pair)]
d.nf_snapshot_release.argtypes=[P];d.nf_snapshot_destroy.argtypes=[P]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
store=d.nf_snapshot_create(32*1024*1024);assert store
received=[];errors=[];last_time=None
@Sink
def consume(context,epoch,data,size):
 global last_time
 try:
  packet=C.string_at(data,size);serial,begin,end,page=struct.unpack_from('<4I',packet,16)
  assert packet==(root/'camera/packet-sequence'/f'scene-{serial:03}.packet').read_bytes()
  assert d.nf_scene_packet_push(store,epoch,data,size)
  received.append((epoch,serial));last_time=end;return 1
 except Exception as error:errors.append(repr(error));return 0
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'');assert d.nf_state(str(root/'driving.state').encode(),0)
assert d.nf_native_scene_sink(consume,None)
epochs=[];retained_checks=0
try:
 for run in range(2):
  if run:
   previous=d.nf_native_scene_epoch();assert d.nf_state(str(root/'driving.state').encode(),0)
   assert d.nf_native_scene_epoch()>previous
   # Consumer must suppress old retained data immediately, before a new push.
   pair=Pair();assert d.nf_snapshot_acquire(store,last_time,0,C.byref(pair))==2
   assert pair.time.epoch!=d.nf_native_scene_epoch();d.nf_snapshot_release(store)
  epoch=d.nf_native_scene_epoch();epochs.append(epoch);last_time=None
  for frame in range(180):
   d.nf_frame(1)
   if last_time is not None:
    pair=Pair();assert d.nf_snapshot_acquire(store,last_time,0,C.byref(pair))==2
    assert pair.time.epoch==epoch
    # Publication has returned and the producer's temporary packet is freed.
    for ptr,size,serial in [(pair.older,pair.older_size,pair.time.older),(pair.newer,pair.newer_size,pair.time.newer)]:
     assert C.string_at(ptr,size)==(root/'camera/packet-sequence'/f'scene-{serial:03}.packet').read_bytes()
    d.nf_snapshot_release(store);retained_checks+=1
  assert [serial for e,serial in received if e==epoch]==list(range(48))
  baseline=json.loads((root/'camera/native-scenes-live-capture-tests.json').read_text())['hashes']
  for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
   path=root/f'camera/live-memory-{name}.bin';d.nf_dump(str(path).encode(),address,size)
   assert hashlib.sha256(path.read_bytes()).hexdigest()==baseline[name]
 assert not errors,errors
 report={'result':'PASS','live_packets_verified':len(received),'retained_pair_checks_after_producer_release':retained_checks,'state_reload_epochs':epochs,'capture_preserves_memory':True,'scope':'Synchronous live publication into retained snapshot storage, including backward state reload. Presentation must reject pairs from old epochs; automatic camera-cut detection and live GPU integration remain pending.'}
 (root/'camera/live-memory-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:
 d.nf_close();assert d.nf_snapshot_destroy(store)
