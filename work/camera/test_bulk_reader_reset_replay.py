"""Independent original/bulk probe replay across actual save-state reloads."""
import ctypes as C,json,hashlib,os,csv
from pathlib import Path
p=Path('work/camera').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=Path('work/race.state').resolve();protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state)}
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];os.environ['NF_TEST_RACING_OWNED_CAPTURE']='1';assert crt._putenv(b'NF_TEST_RACING_OWNED_CAPTURE=1')==0
os.environ['NF_CAPTURE_INDEXED_COPY']='1';assert crt._putenv(b'NF_CAPTURE_INDEXED_COPY=1')==0
inputs=list(csv.DictReader((p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-input.csv').open()))
folder=p/'prototype-runs/bulk-reader-reset-replay-20261010';folder.mkdir(exist_ok=True)
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(context,epoch,data,size):return 1
reports=[];frames=[]
for name in ('viewport-sky-private-capture-probe.dll','viewport-sky-reader-bulk.dll'):
 d=C.CDLL(str(p/name));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_native_scene_refresh.restype=C.c_uint;d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
 for f in ('nf_world_trace','nf_capture'):getattr(d,f).argtypes=[C.c_char_p]
 d.nf_native_model_plan_trace.argtypes=[C.c_char_p,C.c_void_p,C.c_uint]
 read=d.nf_native_owned_frame_read_private;read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];read.restype=C.c_int
 assert d.nf_init(str(rom).encode(),b'');owned=rom.read_bytes();assert d.nf_native_scene_sink(sink,None);assert d.nf_live_visibility_enable(owned,len(owned),16*1024*1024);assert d.nf_bitmap_text_enable(1);assert d.nf_layer_queue_enable(1)
 plan=(p/'road-correction-reciprocal.bin').read_bytes();packets=[];epochs=[];old=None
 try:
  for generation in range(2):
   before_packets=len(packets)
   assert d.nf_state(str(state).encode(),0)==1;epoch=d.nf_native_scene_epoch();epochs.append(epoch)
   if old is not None:
    sent=C.create_string_buffer(b'X'*16);written=C.c_size_t(123);assert read(old[0],old[1],sent,16,C.byref(written))==0 and written.value==123 and sent.raw==b'X'*16+b'\0'
   assert d.nf_owned_graph_live_enable(1);assert d.nf_world_trace(str(folder/(name+str(generation)+'.world')).encode());d.nf_capture(str(folder/(name+str(generation)+'.hooks')).encode());assert d.nf_native_model_plan_trace(str(folder/(name+str(generation)+'.models')).encode(),plan,len(plan))
   for input_row in inputs:
    if d.nf_native_scene_refresh()>=8750:break
    d.nf_frame(int(input_row['keys']))
   for index in range(16):
    refresh=d.nf_native_scene_refresh();d.nf_frame(1);size=C.c_size_t()
    if read(epoch,refresh,None,0,C.byref(size))!=1:continue
    buf=C.create_string_buffer(size.value);assert read(epoch,refresh,buf,len(buf),C.byref(size))==1;packets.append(buf.raw);old=(epoch,refresh)
   assert len(packets)-before_packets>=2,(name,generation,len(packets)-before_packets)
   print('RESET_REPLAY_CAPTURED',name,generation,len(packets)-before_packets,flush=True)
  assert epochs[1]>epochs[0];frames.append(packets);reports.append(dict(probe=name,epochs=epochs,frames=len(packets)))
 finally:d.nf_close()
assert len(frames[0])==len(frames[1])>=8 and frames[0]==frames[1]
assert all(hashlib.sha256(x.read_bytes()).hexdigest()==h for x,h in ((Path(k),v) for k,v in protected.items()))
out=dict(result='PASS_INDEPENDENT_ORIGINAL_BULK_RESET_FRAME_PARITY',probes=reports,matching_frames=len(frames[0]),scope='Two independent original/bulk probe cores, same ROM/state/input, actual state reload epoch change and stale epoch rejection, all complete packet bytes equal. Synchronous component replay, not playable timing/4K render qualification.')
(folder/'audit.json').write_text(json.dumps(out,indent=2));print(out)
