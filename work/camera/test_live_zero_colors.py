from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));P=C.c_void_p;U=C.c_uint32
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_epoch.restype=C.c_uint64
d.nf_layer_queue_zero_colors.argtypes=[C.c_uint64,U,P,U]
d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,U,U,P,U]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'') and d.nf_state(b'work/driving.state',0)
try:
 assert d.nf_layer_queue_enable(1)
 for i in range(20):d.nf_frame(1)
 epoch=d.nf_native_scene_epoch();latest=d.nf_layer_queue_latest();verified=0;distinct=[]
 for refresh in range(latest-3,latest+1):
  colors=C.create_string_buffer(320);assert d.nf_layer_queue_zero_colors(epoch,refresh,colors,320)
  values=struct.unpack('<160H',colors.raw);distinct.append(len(set(values)))
  for row in range(160):
   captured=C.create_string_buffer(34944);assert d.nf_layer_queue_hud_row(epoch,refresh,row,captured,34944)
   assert struct.unpack_from('<2I',captured.raw)==(refresh,row)
   assert struct.unpack_from('<H',captured.raw,128+0x8000)[0]==values[row];verified+=1
 for bad_epoch,bad_refresh,size in [(epoch+1,latest,320),(epoch,latest+1,320),(epoch,latest,319)]:
  out=C.create_string_buffer(b'X'*320,320);assert not d.nf_layer_queue_zero_colors(bad_epoch,bad_refresh,out,size) and out.raw==b'X'*320
 assert max(distinct)>1
 report=dict(result='PASS',exact_owned_rows=verified,refreshes=4,distinct_row_colors=distinct,atomic_identity_rejections=3,scope='Live compact exact-refresh index0 copyout matches retained hardware row palette bytes; GPU live tagged models/fullscene motion still pending.')
 (p/'live-zero-colors-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:d.nf_close()
