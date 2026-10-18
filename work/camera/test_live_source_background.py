import ctypes as C,os,json,time,struct
from pathlib import Path
from PIL import Image
cache=Path(os.environ['TEMP'])/'NFSUG-Native-Geometry-Preview-20261014'
crt=C.CDLL('msvcrt.dll');crt._putenv.argtypes=[C.c_char_p]
for text in (b'NF_LAYER_DIRTY=1',b'NF_TEST_RACING_OWNED_CAPTURE=1'):assert crt._putenv(text)==0
with os.add_dll_directory(str(cache)):
 d=C.CDLL(str(cache/'nfsprobe.dll'))
 d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
 d.nf_native_scene_epoch.restype=C.c_uint64;d.nf_native_scene_refresh.restype=C.c_uint
 d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_layer_queue_text_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint]
 d.nf_native_model_plan_trace.argtypes=[C.c_char_p,C.c_void_p,C.c_uint]
 d.nf_native_live_background_vram.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
 d.nf_native_live_background_coverage.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
 assert d.nf_init(os.fsencode(cache/'game.gba'),b'')
 try:
  d.nf_60(0);assert d.nf_state(os.fsencode(cache/'checkpoint.state'),0)
  Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);sink=Sink(lambda *args:1)
  d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];assert d.nf_native_scene_sink(sink,None);assert d.nf_native_scene_multimodel(1)
  assert d.nf_layer_queue_enable(1);assert d.nf_bitmap_text_enable(1)
  data=Path(r'Y:\CODEX\NFSUG-Native-PC-Port\work\camera\road-correction-reciprocal.bin').read_bytes();table=C.create_string_buffer(data)
  assert len(data)==131072 and d.nf_native_model_plan_trace(b'',table,len(data))
  d.nf_world_trace.argtypes=[C.c_char_p];assert d.nf_world_trace(b'')
  begin=time.perf_counter()
  for _ in range(80):d.nf_frame(1)
  elapsed=time.perf_counter()-begin;epoch=d.nf_native_scene_epoch();refresh=d.nf_native_live_latest_frame()
  v=C.create_string_buffer(0x18000);m=C.create_string_buffer(0x18000)
  assert refresh and d.nf_native_live_background_vram(refresh,v,len(v)) and d.nf_native_live_background_coverage(refresh,m,len(m))
  row=C.create_string_buffer(d.nf_layer_hud_row_size());ix=C.create_string_buffer(240);cov=C.create_string_buffer(240);rgba=bytearray(240*160*4);text_rows=0
  for y in range(160):
   assert d.nf_layer_queue_hud_row(epoch,refresh,y,row,len(row))
   text_rows+=bool(d.nf_layer_queue_text_row(epoch,refresh,y,ix,cov,240))
   page=0xa000 if struct.unpack_from('<H',row.raw,8)[0]&16 else 0
   for x in range(240):
    at=page+y*240+x
    if not m.raw[at]:continue
    c=struct.unpack_from('<H',row.raw,32896+v.raw[at]*2)[0]
    rgb=[((c>>shift&31)<<3)|((c>>shift&31)>>2) for shift in (0,5,10)]
    rgba[(y*240+x)*4:(y*240+x+1)*4]=bytes(rgb+[255])
  out=Path(r'C:\NFSUG-Workspace\NFSUG-packet-live-local\bounded-build')
  Image.frombytes('RGBA',(240,160),bytes(rgba)).save(out/'live-source-background.png')
  result=dict(epoch=epoch,refresh=refresh,text_rows=text_rows,frames=80,unpaced_seconds=elapsed,covered_pixels=sum(rgba[i]!=0 for i in range(3,len(rgba),4)))
  (out/'live-source-background.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 finally:d.nf_close()