import ctypes as C,hashlib,json
from pathlib import Path
p=Path('work/camera').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';raw=rom.read_bytes();protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state)}
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for value in (b'NF_CAPTURE_INDEXED_COPY=1',b'NF_TEST_RACING_OWNED_CAPTURE=1'):assert crt._putenv(value)==0
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-state-parity-20261006');out.mkdir(parents=True,exist_ok=True);results={}
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(context,epoch,data,size):return 1
for name in ('visibility-probe-wide.dll','sky-caller-probe.dll'):
 d=C.CDLL(str(p/name));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];assert d.nf_native_scene_sink(sink,None);assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);assert d.nf_world_trace(b'') and d.nf_owned_graph_live_enable(1)
 try:
  for i in range(640):d.nf_frame(1|(32 if 80<=i<400 else 16 if 400<=i<600 else 0))
  blocks={}
  for label,base,size in (('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000),('palette',0x05000000,1024),('oam',0x07000000,1024)):
   target=out/(name+'-'+label+'.bin');d.nf_dump(str(target).encode(),base,size);data=target.read_bytes();assert len(data)==size;blocks[label]=data
  results[name]=blocks
 finally:d.nf_world_trace(None);d.nf_close()
for label in results['visibility-probe-wide.dll']:assert results['visibility-probe-wide.dll'][label]==results['sky-caller-probe.dll'][label],label
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==h for x,h in protected.items())
(out/'tests.json').write_text(json.dumps(dict(result='PASS',original_updates=640,matched_bytes=sum(map(len,results['sky-caller-probe.dll'].values())),scope='Identical scripted original updates with capture enabled: full EWRAM/IWRAM/VRAM/palette/OAM exact versus active bridge; not live timing or GPU interpolation'),indent=2));print('PASS 640-update native sky state parity')
