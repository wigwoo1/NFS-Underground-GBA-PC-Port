"""Match completed packets with their original mode-4 background page.
Capture after nf_frame returns, never reenter the emulator from its callback.
This deliberately excludes hardware sprites/other display layers.
"""
from pathlib import Path
import ctypes as C,struct,json
from PIL import Image
root=Path('work').resolve();out=root/'camera'
d=C.CDLL(str(root/'nfsprobe.dll'))
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
d.nf_read.argtypes=[C.c_uint32,C.c_int];d.nf_read.restype=C.c_uint32
targets={0,40,200};pending=[];errors=[];metadata=[]
@Sink
def receive(context,epoch,ptr,size):
 try:
  data=C.string_at(ptr,size);serial=struct.unpack_from('<I',data,16)[0]
  if serial in targets or serial-1 in targets:pending.append((serial,data))
  return 1
 except Exception as error:errors.append(repr(error));return 0
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(receive,None)
 for frame in range(850):
  d.nf_frame(1)
  for serial,data in pending:
   (out/f'reference-scene-{serial}.packet').write_bytes(data)
   if serial not in targets:continue
   begin,end,page=struct.unpack_from('<3I',data,20);display=d.nf_read(0x04000000,2)
   assert display&7==4 and (display>>4)&1==page
   pp=out/f'reference-scene-{serial}-page.bin';pal=out/f'reference-scene-{serial}-palette.bin'
   d.nf_dump(str(pp).encode(),0x06000000+page*0xa000,240*160)
   d.nf_dump(str(pal).encode(),0x05000000,512)
   palette=struct.unpack('<256H',pal.read_bytes())
   colors=[tuple(((v>>shift)&31)*255//31 for shift in (0,5,10)) for v in palette]
   rgb=bytes(c for index in pp.read_bytes() for c in colors[index])
   Image.frombytes('RGB',(240,160),rgb).save(out/f'reference-scene-{serial}-gba.png')
   metadata.append(dict(serial=serial,begin=begin,end=end,page=page,dispcnt=display,read_after_original_step=frame+1))
  pending.clear()
 assert not errors and {r['serial'] for r in metadata}==targets
finally:d.nf_close()
(out/'scene-reference-capture.json').write_text(json.dumps(dict(scenes=metadata,scope='Original completed mode-4 bitmap page and palette, excluding hardware sprites/other display layers. Native replay must use phase zero of this packet and its successor.'),indent=2))
print(metadata)
