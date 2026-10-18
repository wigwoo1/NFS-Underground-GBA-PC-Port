from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera').resolve();root=p.parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];d.nf_read.argtypes=[C.c_uint32,C.c_int];d.nf_read.restype=C.c_uint32
assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'') and d.nf_state(str(root/'driving.state').encode(),0)
rows=[]
try:
 for frame in range(721):
  d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
  if frame not in (0,179,499,719):continue
  files={}
  for name,base,size in [('oam',0x07000000,1024),('vram',0x06000000,0x18000),('palette',0x05000000,1024),('io',0x04000000,0x60)]:
   f=p/f'layer-inventory-{frame}-{name}.bin';d.nf_dump(str(f).encode(),base,size);files[name]=f.read_bytes()
  sprites=[]
  for index in range(128):
   a,b,c,_=struct.unpack_from('<4H',files['oam'],index*8)
   if not(a&256) and a&512:continue
   sprites.append(dict(index=index,x=b&511,y=a&255,affine=bool(a&256),double_size=bool(a&512),mode=(a>>10)&3,color8=bool(a&8192),shape=a>>14,size=b>>14,tile=c&1023,priority=(c>>10)&3,palette=c>>12,matrix=(b>>9)&31 if a&256 else None))
  dims=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
  visible=[]
  for obj in sprites:
   if obj['tile']<512 or obj['shape']>=3 or obj['mode']==3:continue
   w,h=dims[obj['shape']][obj['size']];scale=2 if obj['affine'] and obj['double_size'] else 1;x=obj['x'] if obj['x']<256 else obj['x']-512;y=obj['y'] if obj['y']<160 else obj['y']-256
   if x<240 and x+w*scale>0 and y<160 and y+h*scale>0:visible.append(obj['index'])
  shadow=C.create_string_buffer(0x60);d.nf_display_registers.argtypes=[C.c_void_p,C.c_uint];assert d.nf_display_registers(shadow,0x60);sentinel=C.create_string_buffer(b'Q'*0x60,0x60);assert not d.nf_display_registers(sentinel,0x5f) and sentinel.raw==b'Q'*0x60
  io=shadow.raw;(p/f'layer-inventory-{frame}-register-shadow.bin').write_bytes(io);regs={name:struct.unpack_from('<H',io,offset)[0] for name,offset in [('display',0),('bg0',8),('bg1',10),('bg2',12),('bg3',14),('blend',80),('alpha',82),('brightness',84)]}
  rows.append(dict(refresh=frame+1,registers=regs,enabled_layers=[name for bit,name in enumerate(('bg0','bg1','bg2','bg3','obj'),8) if regs['display']&(1<<bit)],bus_io_diff_halfwords=sum(files['io'][i:i+2]!=io[i:i+2] for i in range(0,0x60,2)),active_oam_records=sprites,viewport_intersecting_sprite_indices=visible))
finally:d.nf_close()
report=dict(scope='Original hardware layer inventory for native sprite/background recovery; post-refresh owned register shadows and memory; invalid-size atomic rejection; no scanline latch or rendering verification',samples=rows);(p/'layer-inventory-tests.json').write_text(json.dumps(report,indent=2))
for r in rows:print(r['refresh'],r['enabled_layers'],len(r['active_oam_records']),sum(x['affine'] for x in r['active_oam_records']),sum(x['color8'] for x in r['active_oam_records']),r['registers'])
