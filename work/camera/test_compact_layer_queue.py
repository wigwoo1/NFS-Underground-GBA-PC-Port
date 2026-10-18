from pathlib import Path
import ctypes as C,hashlib,json,time
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint];d.nf_layer_capture_row.argtypes=[C.c_uint,C.c_void_p,C.c_uint];d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint];d.nf_pixels.restype=C.c_void_p;d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
def init():assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
def keys(frame):return 1|(32 if 180<=frame<500 else 16 if frame>=500 else 0)
def ram(prefix):
 result=[]
 for name,addr,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'{prefix}-{name}.bin';d.nf_dump(str(path).encode(),addr,size);result.append(hashlib.sha256(path.read_bytes()).hexdigest())
 return result
init();timings=[]
try:
 for frame in range(499):d.nf_frame(keys(frame))
 assert d.nf_layer_queue_enable(1) and d.nf_layer_capture_arm();d.nf_frame(keys(499));refresh=d.nf_layer_queue_latest();epoch=d.nf_native_scene_epoch();size=d.nf_layer_row_size();a=C.create_string_buffer(size);b=C.create_string_buffer(size);saved=[];hud_size=d.nf_layer_hud_row_size();assert hud_size==34944;hud=C.create_string_buffer(hud_size);hud_hashes=[];signatures=[];upper_signatures=[]
 for y in range(160):
  assert d.nf_layer_queue_row(epoch,refresh,y,a,size) and d.nf_layer_capture_row(y,b,size) and a.raw==b.raw;saved.append(hashlib.sha256(a.raw).hexdigest());assert d.nf_layer_queue_hud_row(epoch,refresh,y,hud,hud_size) and hud.raw==a.raw[:128]+a.raw[128+0x10000:];hud_hashes.append(hashlib.sha256(hud.raw).hexdigest());h=hud.raw;signatures.append(hashlib.sha256(h[8:12]+h[20:22]+h[72:94]+h[128:]).hexdigest());upper_signatures.append(hashlib.sha256(h[8:12]+h[20:22]+h[72:94]+h[128+0x4000:]).hexdigest())
 source_hash=hashlib.sha256(C.string_at(d.nf_pixels(),38400*4)).hexdigest()
 for frame in range(500,508):
  t=time.perf_counter_ns();d.nf_frame(keys(frame));timings.append(time.perf_counter_ns()-t)
 for y in range(160):assert d.nf_layer_queue_row(epoch,refresh,y,a,size) and hashlib.sha256(a.raw).hexdigest()==saved[y]
 for y in range(160):assert d.nf_layer_queue_hud_row(epoch,refresh,y,hud,hud_size) and hashlib.sha256(hud.raw).hexdigest()==hud_hashes[y]
 bytes8=d.nf_layer_queue_bytes();sentinel=C.create_string_buffer(b'Q'*size,size);assert not d.nf_layer_queue_row(epoch+1,refresh,0,sentinel,size) and sentinel.raw==b'Q'*size
 for frame in range(508,517):d.nf_frame(keys(frame))
 assert not d.nf_layer_queue_row(epoch,refresh,0,sentinel,size) and sentinel.raw==b'Q'*size;latest=d.nf_layer_queue_latest();assert d.nf_layer_queue_row(epoch,latest,159,a,size);peak=d.nf_layer_queue_bytes();hashes=ram('layer-queue-final');pixelhash=hashlib.sha256(C.string_at(d.nf_pixels(),38400*4)).hexdigest()
 assert d.nf_state(str(p.parent/'driving.state').encode(),0) and not d.nf_layer_queue_row(epoch,latest,159,sentinel,size) and sentinel.raw==b'Q'*size
finally:d.nf_close()
init()
try:
 for frame in range(517):d.nf_frame(keys(frame))
 assert ram('layer-queue-baseline')==hashes and hashlib.sha256(C.string_at(d.nf_pixels(),38400*4)).hexdigest()==pixelhash
finally:d.nf_close()
r=dict(bitmap_upper_obj_state_spans=1+sum(a!=b for a,b in zip(upper_signatures,upper_signatures[1:])),hud_row_bytes=hud_size,full_row_bytes=size,compact_rows_exact=160,compact_delayed_rows_exact=160,prospective_hud_state_spans=1+sum(a!=b for a,b in zip(signatures,signatures[1:])),result='PASS',rows_compared_to_single_capture=160,delayed_refreshes=8,delayed_rows_unchanged=160,retention_slots=16,eviction_rejected=True,load_state_invalidated=True,wrong_epoch_rejected=True,queue_bytes_after9=bytes8,queue_bytes_after16=peak,simulation_with_capture_max_ms=max(timings)/1e6,ram_pixel_parity=True,scope='Refresh/epoch indexed owned layer queue; no host scene/HUD integration or60fps proof');(p/'compact-layer-queue-tests.json').write_text(json.dumps(r,indent=2));print(r)

