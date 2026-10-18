import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/capture-cycles-20261007');cp.mkdir(exist_ok=True)
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(*args):return 1
runs=[]
for name in ['viewport-sky-capture-probe.dll','viewport-sky-cycles-probe.dll']:
 d=C.CDLL(str((p/name).resolve()));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p;d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_visibility_capture.argtypes=[C.c_char_p,C.c_uint];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
 assert d.nf_init(rom,b'') and d.nf_state(b'work/race.state',0);assert d.nf_native_scene_sink(sink,None);assert d.nf_owned_graph_live_enable(1);assert d.nf_visibility_capture(str(cp/(name+'.builder.bin')).encode(),0);d.nf_capture_profile_enable(1)
 pixels=[];cycles=[];layers=[];graphs=[]
 d.nf_native_scene_epoch.restype=C.c_uint64
 d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 assert d.nf_layer_queue_enable(1)
 row_size=d.nf_layer_row_size();row=C.create_string_buffer(row_size)
 try:
  for i in range(160):
   d.nf_frame(1);pixels.append(hashlib.sha256(C.string_at(d.nf_pixels(),240*160*4)).hexdigest())
   epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest();digest=hashlib.sha256()
   for y in range(160):
    assert d.nf_layer_queue_row(epoch,refresh,y,row,row_size);digest.update(row.raw)
   layers.append(dict(refresh=refresh,hash=digest.hexdigest()))
   closed=d.nf_owned_graph_closed_latest()
   if closed and (not graphs or graphs[-1]['refresh']!=closed):
    size=C.c_size_t();assert d.nf_owned_graph_closed_read(epoch,closed,None,0,C.byref(size));raw=C.create_string_buffer(size.value);assert d.nf_owned_graph_closed_read(epoch,closed,raw,size.value,C.byref(size))
    graphs.append(dict(refresh=closed,hash=hashlib.sha256(raw.raw).hexdigest(),bytes=size.value))
   if 'cycles' in name:
    v=(C.c_uint64*3)();assert d.nf_capture_cycles_read(v);assert v[0]>=v[1]+v[2]>0;cycles.append(list(v))
  ram={}
  for label,address,size in [('ewram',0x02000000,262144),('iwram',0x03000000,32768)]:
   out=cp/(name+'.'+label);d.nf_dump(str(out).encode(),address,size);ram[label]=hashlib.sha256(out.read_bytes()).hexdigest()
 finally:d.nf_close()
 runs.append(dict(name=name,pixels=pixels,ram=ram,cycles=cycles,layers=layers,graphs=graphs))
assert runs[0]['layers']==runs[1]['layers'] and runs[0]['graphs']==runs[1]['graphs'] and runs[0]['graphs']
assert runs[0]['pixels']==runs[1]['pixels'] and runs[0]['ram']==runs[1]['ram']
(cp/'snapshot-parity.json').write_text(json.dumps(dict(result='PASS',frames=160,runs=runs,scope='160originalvideo/full160hardware-row snapshots plus all closed graph packets in this route and finalRAMexact; does not prove every scene/sky transport or live performance'),indent=2));print('160 original-video frames and final RAM exact; capture execution counters valid')
