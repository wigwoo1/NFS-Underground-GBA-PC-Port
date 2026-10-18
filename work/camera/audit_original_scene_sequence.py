"""Capture source-page reference at each retained complete-scene boundary."""
from pathlib import Path
import ctypes as C,csv,json,struct,hashlib,sys
from PIL import Image,ImageDraw
p=Path('work/camera').resolve();o=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';multi='--multimodel' in sys.argv;stem='original-multimodel-completed' if multi else 'original-completed-sequence';ex=json.loads((o/('source-order-multimodel-exports.json' if multi else 'original-pose-endpoint-exports.json')).read_text())['exports'];targets={e['identity'][3]+1:e for e in ex};assert len(targets)==len(ex)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint;d.nf_display_registers.argtypes=[C.c_void_p,C.c_uint]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
rows=[];canvas=Image.new('RGB',(960,180*((len(ex)+3)//4)));draw=ImageDraw.Draw(canvas)
d.nf_native_scene_refresh.restype=C.c_uint
try:
 keys=(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0) for i in range(3583)) if multi else (int(r['keys']) for r in csv.DictReader((p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-input.csv').open()))
 for key in keys:
  d.nf_frame(key);refresh=d.nf_native_scene_refresh()
  if refresh in targets:
   e=targets[refresh];serial=e['identity'][1];registers=(C.c_ubyte*0x60)();assert d.nf_display_registers(registers,0x60);shadow=bytes(registers);control=struct.unpack_from('<H',shadow)[0];base=0x0600a000 if control&16 else 0x06000000
   packet=Path(e['path']).read_bytes();packet_page=struct.unpack_from('<I',packet,28)[0];assert packet_page==bool(control&16),(serial,packet_page,control)
   palette=[d.nf_read(0x05000000+i*2,2)&65535 for i in range(256)];page=bytes(d.nf_read(base+i,1)&255 for i in range(38400));rgb=bytes(((palette[index]>>shift)&31)*255//31 for index in page for shift in (0,5,10));im=Image.frombytes('RGB',(240,160),rgb);im.save(o/f'{stem}-scene{serial}.png');j=len(rows);canvas.paste(im,(j%4*240,j//4*180+20));draw.text((j%4*240+3,j//4*180+3),f'{serial}: completed at {refresh}',fill='white')
   rows.append(dict(serial=serial,source_begin=e['identity'][2],source_end=e['identity'][3],read_update=refresh,page=hex(base),page_matches_packet=True,page_sha256=hashlib.sha256(page).hexdigest(),index204_pixels=page.count(204),palette204=hex(palette[204]),bg2_affine_hex=shadow[0x20:0x30].hex()))
  if refresh>=max(targets):break
finally:d.nf_close()
assert len(rows)==len(ex) and hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)];canvas.save(o/f'{stem}-contact.png')
(o/f'{stem}-audit.json').write_text(json.dumps(dict(result='PASS',scenes=rows,rom_state_unchanged=True,scope='Selected raw mode4 pages after completed source-scene flips; page identity matches packet. Excludes hardware HUD/background and does not establish continuous native coverage or 60fps.'),indent=2));print(json.dumps([dict(serial=r['serial'],red_index_pixels=r['index204_pixels']) for r in rows],indent=2))
