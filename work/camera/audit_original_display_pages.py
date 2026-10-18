"""Read-only exact-route page chronology and captured writer final-byte audit."""
from pathlib import Path
import ctypes as C,csv,struct,json,hashlib,collections
from PIL import Image
p=Path('work/camera').resolve();out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research'
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state'
hashes=[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)];rombytes=rom.read_bytes()
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_read.argtypes=[C.c_uint,C.c_int];d.nf_read.restype=C.c_uint
d.nf_display_registers.argtypes=[C.c_void_p,C.c_uint]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
def read(a,n):return bytes(d.nf_read(a+i,1)&255 for i in range(n))
chronology=[];pages={}
try:
 for row in csv.DictReader((p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-input.csv').open()):
  d.nf_frame(int(row['keys']));refresh=int(row['after'])
  if 8877<=refresh<=8886:
   registers=(C.c_ubyte*0x60)();assert d.nf_display_registers(registers,0x60);shadow=bytes(registers)
   control=struct.unpack_from('<H',shadow)[0];chronology.append(dict(refresh=refresh,dispcnt=hex(control),selected_page=hex(0x0600a000 if control&16 else 0x06000000),bg2_affine_hex=shadow[0x20:0x30].hex()))
  if refresh==8882:
   palette=struct.unpack('<256H',read(0x05000000,512))
   for base in (0x06000000,0x0600a000):
    data=read(base,240*160);pages[base]=data
    rgb=bytes(channel for index in data for channel in tuple(((palette[index]>>shift)&31)*255//31 for shift in (0,5,10)))
    Image.frombytes('RGB',(240,160),rgb).save(out/f'original-8882-page-{base:08x}.png')
  if refresh>=8886:break
finally:d.nf_close()
assert hashes==[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)]
capture=json.loads((out/'original-wall-column-audit.json').read_text());summary=collections.defaultdict(collections.Counter)
for column in capture['selected_columns']:
 state=column['state'];destination=int(column['destination'],16)+(state[2]*(state[1]>>14))*2
 for source in column['source_addresses']:
  value=rombytes[source-0x08000000]
  if value:
   base=0x0600a000 if destination>=0x0600a000 else 0x06000000;index=destination-base
   assert 0<=index<len(pages[base])
   summary[column['texture']]['written']+=1;summary[column['texture']]['final_byte_equal' if pages[base][index]==value else 'later_overdraw']+=1
   summary[column['texture']]['final_pair_equal' if pages[base][index:index+2]==bytes((value,value)) else 'pair_later_difference']+=1
  destination+=state[2]*2
report=dict(result='AUDITED',page_read_update=8882,chronology=chronology,writer_final_page_summary={k:dict(v) for k,v in summary.items()},rom_state_unchanged=True,scope='Raw mode4 framebuffer pages read through page flip and actual display-register chronology; raw page palette image excludes affine/background/HUD composition. Earlier wall bytes can be legitimately overwritten by later scene commands.')
(out/'original-display-page-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
