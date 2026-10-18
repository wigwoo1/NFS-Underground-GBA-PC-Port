"""Source hardware menu layers, reconstructed without reading framebuffer as input."""
import ctypes as C,hashlib,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/lifecycle-hardware';out.mkdir(exist_ok=True);d=C.CDLL(str(p/'visibility-probe-wide.dll'));n=C.CDLL(str(p/'obj-tile.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint];d.nf_pixels.restype=C.c_void_p
f=n.nf_obj_mode4_window_scanline;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]*5+[C.c_void_p]*2+[C.c_uint,C.c_void_p]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';checks=[]
for name in ['stage-0','stage-2','stage-6','menu-2','menu-4','menu-5']:
 state=p.parent/'fix-menu'/(name+'.state');before=hashlib.sha256(state.read_bytes()).hexdigest();assert d.nf_init(rom,b'') and d.nf_state(str(state).encode(),0) and d.nf_layer_queue_enable(1)
 try:
  for _ in range(40):d.nf_frame(0)
  refresh=d.nf_layer_queue_latest();epoch=d.nf_native_scene_epoch();buf=C.create_string_buffer(100480);decoded=(C.c_uint32*38400)();reference=C.string_at(d.nf_pixels(),38400*4);mismatches=[];rowhashes=[]
  for y in range(160):
   assert d.nf_layer_queue_row(epoch,refresh,y,buf,100480);b=buf.raw;assert struct.unpack_from('<2I',b)==(refresh,y);regs=b[8:104];m=list(struct.unpack_from('<6i',b,104));matrix=(C.c_int32*6)(*m);v=b[128:98432];pal=b[98432:99456];o=b[99456:100480];get=lambda offset:struct.unpack_from('<H',regs,offset)[0];window=(C.c_uint16*6)(*struct.unpack_from('<6H',regs,64));assert f(v,len(v),pal,len(pal),o,len(o),get(0),get(12),get(80),get(82),get(84),matrix,window,y,C.byref(decoded,y*240*4))
   for x in range(240):
    i=y*240+x
    if (decoded[i]&0xffffff)!=(struct.unpack_from('<I',reference,i*4)[0]&0xffffff):mismatches.append([x,y])
   rowhashes.append(hashlib.sha256(b).hexdigest())
  assert not mismatches,(name,mismatches[:8])
  sentinel=(C.c_uint32*240)(*([0x12345678]*240))
  assert not f(v,len(v),pal,len(pal),o,len(o),get(0),get(12),get(80),get(82),get(84),matrix,window,160,sentinel)
  assert list(sentinel)==[0x12345678]*240
  assert not f(v,len(v),pal,len(pal),o,len(o),get(0)|0x8000,get(12),get(80),get(82),get(84),matrix,window,y,sentinel)
  assert list(sentinel)==[0x12345678]*240
  checks.append(dict(checkpoint=name,source_state_sha256=before,refresh=refresh,mismatched_pixels=len(mismatches),first_mismatches=mismatches[:8],row_hashes=rowhashes));print(name,len(mismatches),flush=True)
 finally:d.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==before
(out/'scanline-report.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Source retained VRAM/palette/OAM/register/affine/window reconstruction at original240x160 scanline coordinates. Framebuffer only compared as reference, never decodeinput. Direct scanline bitmap+OBJ component; not integrated native4K menus or fullgameplay.'),indent=2))
