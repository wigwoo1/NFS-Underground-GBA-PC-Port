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
 pixels=[];cycles=[]
 try:
  for i in range(160):
   d.nf_frame(1);pixels.append(hashlib.sha256(C.string_at(d.nf_pixels(),240*160*4)).hexdigest())
   if 'cycles' in name:
    v=(C.c_uint64*3)();assert d.nf_capture_cycles_read(v);assert v[0]>=v[1]+v[2]>0;cycles.append(list(v))
  ram={}
  for label,address,size in [('ewram',0x02000000,262144),('iwram',0x03000000,32768)]:
   out=cp/(name+'.'+label);d.nf_dump(str(out).encode(),address,size);ram[label]=hashlib.sha256(out.read_bytes()).hexdigest()
 finally:d.nf_close()
 runs.append(dict(name=name,pixels=pixels,ram=ram,cycles=cycles))
assert runs[0]['pixels']==runs[1]['pixels'] and runs[0]['ram']==runs[1]['ram']
(cp/'parity.json').write_text(json.dumps(dict(result='PASS',frames=160,runs=runs,scope='Original core video160frames and finalRAMexact with capture enabled; component cycles notlive performance or complete native snapshot parity'),indent=2));print('160 original-video frames and final RAM exact; capture execution counters valid')
