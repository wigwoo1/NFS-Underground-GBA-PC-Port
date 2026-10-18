from pathlib import Path
import ctypes as C,csv,json,os,hashlib,struct
p=Path('work/camera').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state,p.parent/'nfsprobe.dll')};crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for key in list(os.environ):
 if key.startswith('NF_'):os.environ.pop(key,None);crt._putenv((key+'=').encode())
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_refresh.restype=C.c_uint;d.nf_pixels.restype=C.c_void_p;assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);captured=None;frames=0
try:
 rows=csv.DictReader((p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-input.csv').open())
 for row in rows:
  d.nf_frame(int(row['keys']));frames+=1;refresh=d.nf_native_scene_refresh()
  if refresh==8780:captured=C.string_at(d.nf_pixels(),38400*4);break
  assert refresh<8780,refresh
finally:d.nf_close()
assert captured is not None;(p/'stable-road-original-display-8780-rgba.bin').write_bytes(captured);assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items());pal=(p/'stable-road-display-palettes.bin').read_bytes();last={}
for cmd in (3,4,7):
 samples=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes()
 for offset in range(0,len(samples),5):dest,index=struct.unpack_from('<IB',samples,offset);last[dest]=index
counts={name:0 for name in ('floor','replicate','shift')};unique={name:0 for name in counts};other=0
for dest,index in last.items():
 word=struct.unpack_from('<H',pal,(dest//240)*512+index*2)[0];v=[(word>>(k*5))&31 for k in range(3)];candidates=dict(floor=bytes(x*255//31 for x in v),replicate=bytes((x<<3)|(x>>2) for x in v),shift=bytes(x<<3 for x in v));actual=captured[dest*4:dest*4+3];matching=[name for name,value in candidates.items() if value==actual]
 for name in matching:counts[name]+=1
 if len(matching)==1:unique[matching[0]]+=1
 if not matching:other+=1
report=dict(result='CAPTURED',refresh=8780,frames=frames,rgba_sha256=hashlib.sha256(captured).hexdigest(),counts=counts,uniquely_matching=unique,other_pixels=other,scope='Original mGBA game framebuffer at exact display refresh8780 replaying recorded original inputs from supplied unchanged race state. Road indices/palette comparisons can include occluded destinations; conversion diagnostic not full native rendering proof.');(p/'road-original-display-color-oracle.json').write_text(json.dumps(report,indent=2));print(report)
