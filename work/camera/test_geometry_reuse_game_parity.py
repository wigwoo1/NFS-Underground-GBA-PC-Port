import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/geometry-reuse-20261008');cp.mkdir(exist_ok=True)
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(*args):return 1
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for flag in ('NF_TEST_RACING_OWNED_CAPTURE','NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_DIRECT_CAPTURE_RAM','NF_CAPTURE_INDEXED_COPY'):assert crt._putenv((flag+'=1').encode())==0
ledger=json.loads((p/'prototype-runs/owned-native-1791437067890037300.json').read_text())
model_plan_table=(p/'road-correction-reciprocal.bin').read_bytes();rom_owned=Path(rom.decode()).read_bytes()
runs=[]
for name in ['viewport-sky-capture-probe.dll','viewport-sky-geometry-reuse-probe.dll']:
 d=C.CDLL(str((p/name).resolve()));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p;d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_visibility_capture.argtypes=[C.c_char_p,C.c_uint];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
 assert d.nf_init(rom,b'') and d.nf_state(b'work/race.state',0);assert d.nf_native_scene_sink(sink,None)
 d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_native_model_plan_trace.argtypes=[C.c_char_p,C.c_void_p,C.c_uint]
 assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024);assert d.nf_bitmap_text_enable(1)
 started=False
 for row in ledger['startup_inputs']:
  if row['refresh']>=8749 and not started:
   assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1) and d.nf_owned_graph_live_enable(1)
   assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table));started=True
  d.nf_frame(row['keys'])
 assert started
 pixels=[];cycles=[];layers=[];graphs=[];frames=[]
 d.nf_native_scene_epoch.restype=C.c_uint64
 d.nf_native_owned_frame_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 assert d.nf_layer_queue_enable(1)
 row_size=d.nf_layer_row_size();row=C.create_string_buffer(row_size)
 try:
  for i in range(160):
   d.nf_frame(ledger['inputs'][i]['keys']);pixels.append(hashlib.sha256(C.string_at(d.nf_pixels(),240*160*4)).hexdigest())
   epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest();digest=hashlib.sha256()
   for y in range(160):
    assert d.nf_layer_queue_row(epoch,refresh,y,row,row_size);digest.update(row.raw)
   layers.append(dict(refresh=refresh,hash=digest.hexdigest()))
   closed=d.nf_owned_graph_closed_latest()
   if closed and (not graphs or graphs[-1]['refresh']!=closed):
    size=C.c_size_t();assert d.nf_owned_graph_closed_read(epoch,closed,None,0,C.byref(size));raw=C.create_string_buffer(size.value);assert d.nf_owned_graph_closed_read(epoch,closed,raw,size.value,C.byref(size))
    graphs.append(dict(refresh=closed,hash=hashlib.sha256(raw.raw).hexdigest(),bytes=size.value))
   latest=d.nf_native_live_latest_frame()
   if latest and (not frames or frames[-1]['refresh']!=latest):
    n=C.c_size_t();assert d.nf_native_owned_frame_read(epoch,latest,None,0,C.byref(n))
    packet=C.create_string_buffer(n.value);assert d.nf_native_owned_frame_read(epoch,latest,packet,n.value,C.byref(n))
    frames.append(dict(refresh=latest,bytes=n.value,sha256=hashlib.sha256(packet.raw).hexdigest()))
    sentinel=C.create_string_buffer(b'unchanged',9);bad=C.c_size_t()
    assert not d.nf_native_owned_frame_read(epoch,latest,sentinel,9,C.byref(bad)) and sentinel.raw==b'unchanged'
    assert not d.nf_native_owned_frame_read(epoch+1,latest,sentinel,9,C.byref(bad)) and sentinel.raw==b'unchanged'
   if 'cycles' in name:
    v=(C.c_uint64*3)();assert d.nf_capture_cycles_read(v);assert v[0]>=v[1]+v[2]>0;cycles.append(list(v))
  ram={}
  for label,address,size in [('ewram',0x02000000,262144),('iwram',0x03000000,32768)]:
   out=cp/(name+'.'+label);d.nf_dump(str(out).encode(),address,size);ram[label]=hashlib.sha256(out.read_bytes()).hexdigest()
 finally:d.nf_close()
 runs.append(dict(name=name,pixels=pixels,ram=ram,cycles=cycles,layers=layers,graphs=graphs,complete_frames=frames))
(cp/'attempt-coverage.json').write_text(json.dumps(dict(complete_frame_counts=[len(x['complete_frames']) for x in runs],video_exact=runs[0]['pixels']==runs[1]['pixels'],ram_exact=runs[0]['ram']==runs[1]['ram'],layers_exact=runs[0]['layers']==runs[1]['layers'],graphs_exact=runs[0]['graphs']==runs[1]['graphs']),indent=2))
assert runs[0]['complete_frames']==runs[1]['complete_frames'] and runs[0]['complete_frames']
assert runs[0]['layers']==runs[1]['layers'] and runs[0]['graphs']==runs[1]['graphs'] and runs[0]['graphs']
assert runs[0]['pixels']==runs[1]['pixels'] and runs[0]['ram']==runs[1]['ram']
(cp/'complete-game-parity.json').write_text(json.dumps(dict(result='PASS',frames=160,runs=runs,scope='160originalvideo/full160hardware-row snapshots plus all closed graph packets in this route and finalRAMexact; complete captured frames exact with undersized/wrong-epoch atomic rejection; route diagnostic, not fullgame coverage or live pacing'),indent=2));print('160 original-video frames and RAM exact; complete native capture counts:',[len(x['complete_frames']) for x in runs])



