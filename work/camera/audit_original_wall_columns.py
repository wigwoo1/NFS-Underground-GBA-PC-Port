"""Capture actual original wall writer calls for the exported source scene."""
from pathlib import Path
import ctypes as C,csv,struct,json,hashlib
p=Path('work/camera').resolve();out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research'
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state'
hashes=[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)]
trace=out/'original-wall-column-calls.bin';cycles=p.parent/'span-cycles.csv';old_cycles=cycles.read_bytes() if cycles.exists() else None
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_capture.argtypes=[C.c_char_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
try:
 for row in csv.DictReader((p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-input.csv').open()):
  before=int(row['before'])
  if before==8877:d.nf_capture(str(trace).encode())
  d.nf_frame(int(row['keys']))
  if int(row['after'])==8882:break
 else:raise AssertionError('Missing source scene endpoint')
 d.nf_capture(None)
finally:
 d.nf_close()
 if old_cycles is not None:cycles.write_bytes(old_cycles)
 elif cycles.exists():cycles.unlink()
assert hashes==[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)]
raw=trace.read_bytes();assert len(raw)%140==0
native=C.CDLL(str(p/'native_wall.dll'));native.nfs_wall_unshaded_addresses.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
selected=[]
for offset in range(0,len(raw),140):
 words=struct.unpack_from('<35I',raw,offset);frame,pc=words[:2];regs=words[2:18];state=words[18:35]
 if frame<=8877 or pc!=0x030053e8 or state[9] not in (137853404,138309084):continue
 count=regs[3];assert count<=320
 sources=(C.c_uint*320)();destinations=(C.c_uint*320)();buffer=C.create_string_buffer(struct.pack('<17I',*state))
 assert native.nfs_wall_unshaded_addresses(buffer,regs[1],regs[2],count,sources,destinations)
 width=1<<state[3];base=state[9]
 texels=[(int(a)-base)%width for a in sources[:count]]
 selected.append(dict(refresh=frame,texture=hex(base),width=width,height=state[4],destination=hex(regs[1]),starting_v=regs[2],rows=count,horizontal_texels=sorted(set(texels)),state=list(state),source_addresses=list(sources)[:count]))
assert selected
report=dict(result='CAPTURED',source_interval=[8877,8881],capture_through_update=8882,total_calls=len(raw)//140,selected_columns=selected,rom_state_unchanged=True,scope='Actual original unshaded writer calls through source page flip; source interval selection excludes preceding partial draw. Does not yet compare final native GPU texels or all wall material modes.')
(out/'original-wall-column-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(total_calls=report['total_calls'],selected_columns=len(selected),textures=sorted(set(c['texture'] for c in selected)),horizontal_texels=sorted(set(t for c in selected for t in c['horizontal_texels'])))))
