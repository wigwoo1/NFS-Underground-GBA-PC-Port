from pathlib import Path
import ctypes as C,struct,json,hashlib
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'));n=C.CDLL(str(p/'obj-tile.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p;d.nf_layer_capture_row.argtypes=[C.c_uint,C.c_void_p,C.c_uint];f=n.nf_obj_mode4_window_layer;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16]*5+[C.c_void_p]*3
d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
def ram_hash(prefix):
 hashes=[]
 for name,addr,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  file=p/f'{prefix}-{name}.bin';d.nf_dump(str(file).encode(),addr,size);hashes.append(hashlib.sha256(file.read_bytes()).hexdigest())
 return hashes
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for frame in range(499):d.nf_frame(1|(32 if frame>=180 else 0))
 assert d.nf_layer_capture_arm();d.nf_frame(1|32);assert d.nf_layer_capture_status()==3;size=d.nf_layer_row_size();assert size==100480;sentinel=C.create_string_buffer(b'Q'*size,size);assert not d.nf_layer_capture_row(160,sentinel,size) and sentinel.raw==b'Q'*size;assert not d.nf_layer_capture_row(0,sentinel,size-1) and sentinel.raw==b'Q'*size;buf=C.create_string_buffer(size);out=(C.c_uint32*38400)();ref=C.string_at(d.nf_pixels(),38400*4);rows=[];mismatches=[]
 for y in range(160):
  assert d.nf_layer_capture_row(y,buf,size);b=buf.raw;refresh,row=struct.unpack_from('<2I',b);assert row==y;regs=b[8:104];m=list(struct.unpack_from('<6i',b,104));m[4]-=m[1]*y;m[5]-=m[3]*y;matrix=(C.c_int32*6)(*m);v=b[128:98432];pal=b[98432:99456];o=b[99456:100480];get=lambda off:struct.unpack_from('<H',regs,off)[0];window=(C.c_uint16*6)(*struct.unpack_from('<6H',regs,64));assert f(v,len(v),pal,len(pal),o,len(o),get(0),get(12),get(80),get(82),get(84),matrix,window,out),(y,hex(get(0)))
  for x in range(240):
   i=y*240+x;a=out[i]&0xffffff;r=struct.unpack_from('<I',ref,i*4)[0]&0xffffff
   if a!=r:mismatches.append((y,x,hex(a),hex(r)))
  rows.append(dict(refresh=refresh,row=y,register_hash=hashlib.sha256(regs).hexdigest(),vram_hash=hashlib.sha256(v).hexdigest()))
 # Delayed read must retain owned row bytes through newer emulation.
 assert d.nf_layer_capture_row(159,buf,size);saved=buf.raw
 for _ in range(4):d.nf_frame(1)
 assert d.nf_layer_capture_row(159,buf,size) and buf.raw==saved
 capture_ram=ram_hash('scanline-capture-final');capture_pixel_hash=hashlib.sha256(ref).hexdigest()
 snapshot_bytes=d.nf_layer_capture_bytes();snapshot_pages=d.nf_layer_capture_pages();assert snapshot_bytes<160*size
 report=dict(snapshot_bytes=snapshot_bytes,unique_memory_pages=snapshot_pages,raw_snapshot_bytes=160*size,result='PASS' if not mismatches else 'FAIL',rows=160,compared_pixels=38400,mismatch_count=len(mismatches),first_mismatches=mismatches[:12],delayed_snapshot_unchanged=True,unique_register_states=len({r['register_hash'] for r in rows}),unique_vram_states=len({r['vram_hash'] for r in rows}),scope='Actual scanline-owned refresh500 native hardware layer replay vs original pixels; no live HUD GPU integration')
 (p/'scanline-layer-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:d.nf_close()

assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for frame in range(500):d.nf_frame(1|(32 if frame>=180 else 0))
 baseline_pixel_hash=hashlib.sha256(C.string_at(d.nf_pixels(),38400*4)).hexdigest()
 for _ in range(4):d.nf_frame(1)
 baseline_ram=ram_hash('scanline-baseline-final');assert baseline_ram==capture_ram and baseline_pixel_hash==capture_pixel_hash
 report.update(capture_game_ram_parity=True,original_pixel_hash_parity=True,atomic_rejections=2,ram_hashes=capture_ram)
 (p/'scanline-layer-tests.json').write_text(json.dumps(report,indent=2));print('Capture RAM/pixel parity PASS')
finally:d.nf_close()
