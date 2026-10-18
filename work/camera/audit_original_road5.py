"""Read-only original road entry, palette and completed page capture."""
from pathlib import Path
import ctypes as C,csv,struct,json,hashlib
from PIL import Image
from scene_batches import records
p=Path('work/camera').resolve();o=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
trace=p/'original-road5-scene10.bin'
try:
 for row in csv.DictReader((p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-input.csv').open()):
  if int(row['before'])==8881:assert d.nf_world_trace(str(trace).encode())
  d.nf_frame(int(row['keys']))
  if int(row['after'])==8886:break
 else:raise AssertionError('Missing boundary')
 d.nf_world_trace(None)
 palette=[d.nf_read(0x05000000+i*2,2)&65535 for i in range(256)];page=bytes(d.nf_read(0x06000000+i,1)&255 for i in range(38400))
 rgb=bytes(((palette[index]>>shift)&31)*255//31 for index in page for shift in (0,5,10));Image.frombytes('RGB',(240,160),rgb).save(o/'original-8886-page-06000000.png')
finally:d.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
selected=[]
for e in records(trace):
 if e['pc']!=0x030032f0 or e['blocks'][4][0]!=0x0856b5d0 or e['frame']<=8881:continue
 b=e['blocks'];colors=struct.unpack('<256H',b[67][1]);color=colors[204]
 selected.append(dict(refresh=e['frame'],regs=list(e['regs']),material_hex=b[8][1].hex(),projection_hex=b[3][1].hex(),scratch_hex=b[6][1].hex(),prepared_hex=b[7][1].hex(),texture_address=hex(b[66][0]),texture_indices=sorted(set(b[66][1])),palette204=hex(color),palette204_rgb=[((color>>s)&31)*255//31 for s in (0,5,10)],state_bounds=list(struct.unpack_from('<4H',b[1][1],226))))
assert len(selected)==1
r=dict(result='CAPTURED',road=selected[0],completed_page_update=8886,completed_page_index204_count=page.count(204),rom_state_unchanged=True,scope='Original road-entry palette/prepared data and completed raw framebuffer; pixel-count alone does not prove which draw wrote each byte')
(o/'original-road5-scene10-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
