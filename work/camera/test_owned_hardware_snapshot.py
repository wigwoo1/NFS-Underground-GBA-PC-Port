"""Detached compact hardware snapshot survives updates, eviction and reload."""
import ctypes as C,hashlib,json,threading
from pathlib import Path
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_clone.argtypes=[C.c_uint64,C.c_uint];d.nf_layer_queue_clone.restype=P;d.nf_layer_snapshot_read.argtypes=[P,C.c_uint,P];d.nf_layer_snapshot_destroy.argtypes=[P];d.nf_layer_snapshot_bytes.argtypes=[P];d.nf_layer_snapshot_bytes.restype=C.c_size_t;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,P,C.c_uint];rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';checks=[]
for name in ['stage-0','stage-2','menu-4','menu-5']:
 state=p.parent/'fix-menu'/(name+'.state');state_hash=hashlib.sha256(state.read_bytes()).hexdigest();snapshot=None
 assert d.nf_init(rom,b'') and d.nf_state(str(state).encode(),0) and d.nf_layer_queue_enable(1)
 try:
  for _ in range(40):d.nf_frame(0)
  epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest();assert not d.nf_layer_queue_clone(epoch+1,refresh) and not d.nf_layer_queue_clone(epoch,refresh+100)
  snapshot=d.nf_layer_queue_clone(epoch,refresh);assert snapshot;buf=C.create_string_buffer(100480);hashes=[]
  for y in range(160):assert d.nf_layer_snapshot_read(snapshot,y,buf);hashes.append(hashlib.sha256(buf.raw).hexdigest())
  size=d.nf_layer_snapshot_bytes(snapshot)
  for _ in range(40):d.nf_frame(0)
  assert not d.nf_layer_queue_row(epoch,refresh,0,buf,100480)
  assert d.nf_state(str(state).encode(),0)
  error=[]
  def consumer():
   try:
    local=C.create_string_buffer(100480)
    for y in range(160):assert d.nf_layer_snapshot_read(snapshot,y,local) and hashlib.sha256(local.raw).hexdigest()==hashes[y]
   except BaseException as e:error.append(str(e))
  worker=threading.Thread(target=consumer);worker.start()
  for _ in range(8):d.nf_frame(0)
  worker.join();assert not error,error
  sentinel=C.create_string_buffer(b'Q'*100480,100480);assert not d.nf_layer_snapshot_read(snapshot,160,sentinel) and sentinel.raw==b'Q'*100480
  checks.append(dict(checkpoint=name,epoch=epoch,refresh=refresh,owned_bytes=size,expanded_row_bytes=160*100480,rows_exact_after_eviction_reload=160,concurrent_original_updates=8,invalid_epoch_refresh_rejected=True,invalid_row_atomic=True));print(name,size,flush=True)
 finally:
  if snapshot:d.nf_layer_snapshot_destroy(snapshot)
  d.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==state_hash
out=p/'prototype-runs/lifecycle-hardware/owned-snapshot-report.json';out.write_text(json.dumps(dict(result='PASS',checks=checks,scope='Detached compact sourcehardware pages survive queueeviction/checkpointreload and concurrent consumer reads during8originalupdates. No borrowed bridgeviews; tests read-only. Not yet timeline/threadedGL integration or native4K menus.'),indent=2))
