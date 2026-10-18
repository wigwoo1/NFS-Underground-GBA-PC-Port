"""Verify actual producer/worker menu pixels against original-input source replay."""
import ctypes as C,csv,hashlib,json,math,struct,sys
from pathlib import Path
manifest=Path(sys.argv[1]);s=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=s['prefix'];p=Path(__file__).resolve().parent;rows=list(csv.DictReader(Path(prefix+'-input.csv').open()));draws=list(csv.DictReader(Path(prefix+'-worker.csv').open()));captures=[(i,math.floor(float(r['target']))) for i,r in enumerate(draws[:6])];needed=set(t for i,t in captures);originalhash={name:hashlib.sha256(Path(s[name]).read_bytes()).hexdigest() for name in ('rom','state')};d=C.CDLL(str(p/'visibility-probe-wide.dll'));n=C.CDLL(str(p/'obj-tile.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint];Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
@Sink
def sink(*args):return 1
f=n.nf_obj_mode4_window_scanline;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]*5+[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];pixel=n.nf_obj_bg_backdrop_pixel;pixel.argtypes=[C.c_uint32]*8;pixel.restype=C.c_uint32;expected={};assert d.nf_init(s['rom'].encode(),b'') and d.nf_state(s['state'].encode(),0) and d.nf_native_scene_sink(sink,None) and d.nf_layer_queue_enable(1)
try:
 for tick in rows:
  d.nf_frame(int(tick['keys']));latest=d.nf_layer_queue_latest();epoch=d.nf_native_scene_epoch()
  for refresh in sorted(needed-set(expected)):
   if latest<refresh:continue
   buf=C.create_string_buffer(100480)
   if not d.nf_layer_queue_row(epoch,refresh,0,buf,100480):continue
   frame=bytearray()
   for y in range(160):
    assert d.nf_layer_queue_row(epoch,refresh,y,buf,100480);r=buf.raw;get=lambda offset:struct.unpack_from('<H',r,offset)[0];m=(C.c_int32*6)(*struct.unpack_from('<6i',r,104));window=(C.c_uint16*6)(*struct.unpack_from('<6H',r,72));decoded=(C.c_uint32*240)();v=r[128:98432];pal=r[98432:99456];o=r[99456:100480];assert f(v,len(v),pal,len(pal),o,len(o),get(8),get(20),get(88),get(90),get(92),m,window,y,decoded)
    c=get(98432);bd=0xff000000|sum((((c>>(k*5)&31)<<3)|(c>>(k*5)&31)>>2)<<(k*8) for k in range(3));side=struct.pack('<I',pixel(0,0,0,get(20)&3,bd,get(88),get(90),get(92)));line=bytearray(side*3840)
    for x in range(240):
     left=math.ceil(300+x*13.5-.5);right=math.ceil(300+(x+1)*13.5-.5);line[left*4:right*4]=struct.pack('<I',decoded[x])*(right-left)
    frame.extend(line*(math.ceil((y+1)*13.5-.5)-math.ceil(y*13.5-.5)))
   expected[refresh]=hashlib.sha256(frame).hexdigest()
  if len(expected)==len(needed):break
finally:d.nf_close()
checks=[]
for i,refresh in captures:
 path=Path(prefix+f'-hardware-{i:02d}.rgba');actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==expected[refresh],(i,refresh,actual,expected[refresh]);checks.append(dict(index=i,refresh=refresh,full4K_rgba_sha256=actual))
for name in ('rom','state'):assert hashlib.sha256(Path(s[name]).read_bytes()).hexdigest()==originalhash[name]
report=dict(result='PASS',checks=checks,scope='Actual timed producer/worker menu captures match every4K RGBA byte of CPU source compositor from same original recorded inputs. No screen matching/framebuffer input; staticpixel source sampling previously verified against original. Readback/disk capture is diagnostic, not gameplay60fps proof.');Path(prefix+'-menu-pixel-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
